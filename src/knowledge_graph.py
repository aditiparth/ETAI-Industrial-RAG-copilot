from neo4j import GraphDatabase
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

class KnowledgeGraph:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def clear_graph(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def add_chunk_with_entities(self, chunk):
        """Creates a Document node and links entity nodes to it."""
        with self.driver.session() as session:
            session.run("""
                MERGE (d:Document {chunk_id: $chunk_id})
                SET d.source = $source, d.page = $page, d.doc_type = $doc_type, d.text = $text
            """, chunk_id=chunk["chunk_id"], source=chunk["source"],
                 page=chunk["page"], doc_type=chunk["doc_type"], text=chunk["text"][:500])

            entities = chunk.get("entities", {})
            for tag in entities.get("equipment_tags", []):
                session.run("""
                    MERGE (e:Equipment {tag: $tag})
                    WITH e
                    MATCH (d:Document {chunk_id: $chunk_id})
                    MERGE (d)-[:MENTIONS]->(e)
                """, tag=tag, chunk_id=chunk["chunk_id"])

            for std in entities.get("standards", []):
                session.run("""
                    MERGE (s:Standard {name: $std})
                    WITH s
                    MATCH (d:Document {chunk_id: $chunk_id})
                    MERGE (d)-[:REFERENCES]->(s)
                """, std=std, chunk_id=chunk["chunk_id"])

    def add_chunks_batch(self, chunks, batch_size=100):
        """Write chunks in batches using UNWIND — much faster and more reliable than one-by-one."""
        with self.driver.session() as session:
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]

                doc_data = [{
                    "chunk_id": c["chunk_id"],
                    "source": c["source"],
                    "page": c["page"],
                    "doc_type": c["doc_type"],
                    "text": c["text"][:500]
                } for c in batch]

                session.run("""
                    UNWIND $docs AS doc
                    MERGE (d:Document {chunk_id: doc.chunk_id})
                    SET d.source = doc.source, d.page = doc.page,
                        d.doc_type = doc.doc_type, d.text = doc.text
                """, docs=doc_data)

                equip_data = []
                for c in batch:
                    for tag in c.get("entities", {}).get("equipment_tags", []):
                        equip_data.append({"chunk_id": c["chunk_id"], "tag": tag})
                if equip_data:
                    session.run("""
                        UNWIND $links AS link
                        MERGE (e:Equipment {tag: link.tag})
                        WITH e, link
                        MATCH (d:Document {chunk_id: link.chunk_id})
                        MERGE (d)-[:MENTIONS]->(e)
                    """, links=equip_data)

                std_data = []
                for c in batch:
                    for std in c.get("entities", {}).get("standards", []):
                        std_data.append({"chunk_id": c["chunk_id"], "std": std})
                if std_data:
                    session.run("""
                        UNWIND $links AS link
                        MERGE (s:Standard {name: link.std})
                        WITH s, link
                        MATCH (d:Document {chunk_id: link.chunk_id})
                        MERGE (d)-[:REFERENCES]->(s)
                    """, links=std_data)

                print(f"  Graph batch {i + len(batch)}/{len(chunks)} written")

    def get_related_chunks(self, entity_text):
        """Given an entity mentioned in a query, find all linked documents."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e {tag: $entity})<-[:MENTIONS]-(d:Document)
                RETURN d.chunk_id AS chunk_id, d.text AS text, d.source AS source, d.page AS page, d.doc_type AS doc_type
                UNION
                MATCH (s:Standard {name: $entity})<-[:REFERENCES]-(d:Document)
                RETURN d.chunk_id AS chunk_id, d.text AS text, d.source AS source, d.page AS page, d.doc_type AS doc_type
            """, entity=entity_text)
            return [dict(record) for record in result]

    def get_graph_data(self, limit=200):
        """Fetch nodes and relationships for visualization."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Document)-[r]->(n)
                RETURN d.chunk_id AS doc_id, d.source AS doc_source, d.doc_type AS doc_type,
                       type(r) AS rel_type, labels(n)[0] AS node_type,
                       coalesce(n.tag, n.name) AS node_name
                LIMIT $limit
            """, limit=limit)
            return [dict(record) for record in result]

    def find_entities_in_query(self, query_text):
        """Simple check: does query mention any known equipment tag pattern?"""
        import re
        from src.entity_extraction import EQUIPMENT_PATTERN, STANDARD_PATTERN
        tags = EQUIPMENT_PATTERN.findall(query_text)
        stds = STANDARD_PATTERN.findall(query_text)
        return tags + stds