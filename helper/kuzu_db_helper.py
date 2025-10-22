from operator import le
import kuzu
import json
import os
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

class KuzuSkillGraph:
    """
    KuzuDB integration for storing and managing learning roadmap skills as a graph database.
    """
    
    def __init__(self, db_path: str = "skills_graph.db"):
        """Initialize KuzuDB connection and create schema."""
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        # self._create_schema()
    
    def get_skill_info(self, skill_name: str) -> Dict[str, Any]:
        """Retrieve information for a specific skill."""
        
        # Get skill information
        result = self.conn.execute("""
            MATCH (s:Skill {name: $skill_name})
            RETURN s.id as id, s.order_index as order_index
        """, parameters={"skill_name": skill_name})
        
        skill_info = result.get_next()
        if not skill_info:
            return {"error": f"Skill '{skill_name}' not found"}
        
        return {
            "id": skill_info[0],
            "order_index": skill_info[1]
        }
    
    def get_all_skills(self) -> List[Dict[str, Any]]:
        """Get all skills ordered by their index."""
        result = self.conn.execute("""
            MATCH (s:Skill)
            RETURN s.id as id, s.name as name, s.order_index as order_index
            ORDER BY s.order_index
        """)
        
        skills = []
        while result.has_next():
            row = result.get_next()
            skills.append({
                "id": row[0],
                "name": row[1],
                "order_index": row[2]
            })
        
        return skills
    
    def get_skill_roadmap(self, skill_name: str) -> Dict[str, Any]:
        """Retrieve a complete roadmap for a specific skill."""
        skill_id = f"skill_{skill_name.replace(' ', '_')}"
        
        # Get skill information
        result = self.conn.execute("""
            MATCH (s:Skill {id: $skill_id})
            RETURN s.name as name, s.order_index as order_index
        """, parameters={"skill_id": skill_id})
        
        skill_info = result.get_next()
        if not skill_info:
            return {"error": f"Skill '{skill_name}' not found"}
        
        # Get all learning nodes for this skill
        result = self.conn.execute("""
            MATCH (s:Skill {id: $skill_id})<-[:BELONGS_TO]-(n:LearningNode)
            RETURN n.id as id, n.name as name, n.description as description
            ORDER BY n.name
        """, parameters={"skill_id": skill_id})
        
        nodes = []
        while result.has_next():
            row = result.get_next()
            nodes.append({
                "id": row[0],
                "name": row[1],
                "description": row[2]
            })
        
        # Get all edges for this skill
        result = self.conn.execute("""
            MATCH (s:Skill {id: $skill_id})<-[:BELONGS_TO]-(from:LearningNode)-[:PREREQUISITE]->(to:LearningNode)-[:BELONGS_TO]->(s)
            RETURN from.id as from_id, to.id as to_id
        """, parameters={"skill_id": skill_id})
        
        edges = []
        while result.has_next():
            row = result.get_next()
            edges.append({
                "from": row[0],
                "to": row[1],
                "audience_type": "general"  # Default audience type
            })
        
        return {
            "skill": skill_info[0],
            "order_index": skill_info[1],
            "nodes": nodes,
            "edges": edges
        }
    
    def get_skill_connections(self, skill_name: str) -> Dict[str, List[str]]:
        """Get skills connected to the given skill (both incoming and outgoing)."""
        skill_id = f"skill_{skill_name.replace(' ', '_')}"
        
        # Get outgoing connections (skills this skill connects to)
        result = self.conn.execute("""
            MATCH (s:Skill {id: $skill_id})-[:SKILL_CONNECTION]->(connected:Skill)
            RETURN connected.name as name
        """, parameters={"skill_id": skill_id})
        
        outgoing = []
        while result.has_next():
            row = result.get_next()
            outgoing.append(row[0])
        
        # Get incoming connections (skills that connect to this skill)
        result = self.conn.execute("""
            MATCH (connected:Skill)-[:SKILL_CONNECTION]->(s:Skill {id: $skill_id})
            RETURN connected.name as name
        """, parameters={"skill_id": skill_id})
        
        incoming = []
        while result.has_next():
            row = result.get_next()
            incoming.append(row[0])
        
        return {
            "incoming": incoming,
            "outgoing": outgoing
        }
    
    def get_all_skills(self) -> List[Dict]:
        """Get all skills from the database."""
        result = self.conn.execute("""
            MATCH (s:Skill)
            RETURN s.id as id, s.name as name, s.order_index as order_index
        """)
        
        skills = []
        while result.has_next():
            row = result.get_next()
            skills.append({
                "id": row[0],
                "name": row[1],
                "description": f"Learn {row[1]} skills and concepts",
                "order_index": row[2]
            })
        
        return skills
    
    def get_all_skill_connections(self) -> List[Dict]:
        """Get all skill connections from the database."""
        result = self.conn.execute("""
            MATCH (from:Skill)-[:SKILL_CONNECTION]->(to:Skill)
            RETURN from.id as from_skill, to.id as to_skill
        """)
        
        connections = []
        while result.has_next():
            row = result.get_next()
            connections.append({
                "from_skill": row[0],
                "to_skill": row[1],
                "relationship_type": "prerequisite",  # Default relationship type
                "weight": 1  # Default weight
            })
        
        return connections
    
    def get_skill_by_id(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get a single skill by its id."""
        result = self.conn.execute("""
            MATCH (s:Skill {id: $id})
            RETURN s.id as id, s.name as name, s.order_index as order_index
            LIMIT 1
        """, parameters={"id": skill_id})
        if result.has_next():
            row = result.get_next()
            return {
                "id": row[0],
                "name": row[1],
                "description": f"Learn {row[1]} skills and concepts",
                "order_index": row[2]
            }
        return None

    def get_skill_prerequisites(self, skill_id: str) -> List[Dict[str, Any]]:
        """Get prerequisite skills (incoming skill connections)."""
        result = self.conn.execute("""
            MATCH (pre:Skill)-[:SKILL_CONNECTION]->(s:Skill {id: $id})
            RETURN pre.id as id, pre.name as name
        """, parameters={"id": skill_id})
        skills: List[Dict[str, Any]] = []
        while result.has_next():
            row = result.get_next()
            skills.append({
                "id": row[0],
                "name": row[1]
            })
        return skills

    def get_skill_prerequisites_by_name(self, skill_name: str) -> List[Dict[str, Any]]:
        """Get prerequisite skills (incoming skill connections)."""
        try:
            skill_id = self.get_skill_info(skill_name)["id"]
            result = self.conn.execute("""
                MATCH (pre:Skill)-[:SKILL_CONNECTION]->(s:Skill {id: $id})
                RETURN pre.id as id, pre.name as name
            """, parameters={"id": skill_id})
            skills: List[Dict[str, Any]] = []
            while result.has_next():
                row = result.get_next()
                skills.append({
                    "id": row[0],
                    "name": row[1]
                })
            return skills
        except Exception as e:
            print(f"Error getting skill prerequisites by name: {e}")
            return []

    def get_skill_next_skills(self, skill_id: str) -> List[Dict[str, Any]]:
        """Get next skills (outgoing skill connections)."""
        result = self.conn.execute("""
            MATCH (s:Skill {id: $id})-[:SKILL_CONNECTION]->(next:Skill)
            RETURN next.id as id, next.name as name
        """, parameters={"id": skill_id})
        skills: List[Dict[str, Any]] = []
        while result.has_next():
            row = result.get_next()
            skills.append({
                "id": row[0],
                "name": row[1]
            })
        return skills

    def find_learning_path(self, start_skill: str, end_skill: str) -> List[Dict[str, str]]:
        """Find a learning path between two skills using KuzuDB shortest path."""
        res = self.conn.execute(
            """
            MATCH path = (s1:Skill {name: $start_skill})-[:SKILL_CONNECTION*1..10]-(s2:Skill {name: $end_skill})
            RETURN path
            ORDER BY length(path)
            LIMIT 1;
            """,
            parameters={"start_skill": start_skill, "end_skill": end_skill}
        )
        path: List[Dict[str, str]] = []
        while res.has_next():
            row = res.get_next()
            for node in row[0]["_nodes"]:
                path.append({"id": node["id"], "name": node["name"]})
        print("=================================")
        print("Path objects:", path)
        print("=================================")
        return path
    
    def close(self):
        """Close the database connection."""
        self.conn.close()
