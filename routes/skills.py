from fastapi import HTTPException, APIRouter
from helper.helper import get_kuzu_manager

router = APIRouter(
    prefix="",
    tags=["Skills"],
)

@router.get("/api/skill/{skill_id}")
async def get_skill_details(skill_id: str):
    """Get detailed information about a specific skill."""
    try:
        manager = get_kuzu_manager()
        skill = manager.get_skill_by_id(skill_id)
        
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        # Get related skills (prerequisites and next skills)
        prerequisites = manager.get_skill_prerequisites(skill_id)
        next_skills = manager.get_skill_next_skills(skill_id)
        
        return {
            "id": skill["id"],
            "name": skill["name"],
            "description": skill.get("description", ""),
            "level": skill.get("level", ""),
            "order_index": skill.get("order_index", 0),
            "prerequisites": prerequisites,
            "next_skills": next_skills,
            "total_prerequisites": len(prerequisites),
            "total_next_skills": len(next_skills)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting skill details: {str(e)}")

@router.get("/api/skills/{skill_name}/prerequisites")
async def get_skill_prerequisites(skill_name: str):
    """Get prerequisites for a specific skill."""
    try:
        manager = get_kuzu_manager()
        prerequisites = manager.get_skill_prerequisites_by_name(skill_name)
        return {
            "skill_name": skill_name,
            "prerequisites": prerequisites,
            "total_prerequisites": len(prerequisites)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting skill prerequisites: {str(e)}")


@router.get("/api/skill-path")
async def get_skill_path(start: str = None, end: str = None, user_roadmap_path_id: str = None):
    """Get a learning path between two skills (by name) using KuzuDB graph, or from a user roadmap path.

    Returns a list of skill ids representing the path, and also the corresponding
    edges between consecutive skills for easy highlighting on the client.
    
    Parameters:
    - start, end: Use these to find a path between two skills by name
    - user_roadmap_path_id: Use this to get skills from a saved user roadmap path
    """
    # try:
    manager = get_kuzu_manager()
    
    if start and end:
        print(start, end, "start, end")
        paths = manager.find_learning_path(start, end)
        print(paths, "paths")
        if not paths:
            return {"path": [], "edges": []}

        edges = []
        for i in range(len(paths) - 1):
            source = paths[i]["id"]
            target = paths[i + 1]["id"]
            edges.append({
                "id": f"{source}-{target}",
                "source": source,
                "target": target
            })

        return {
            "path": paths,
            "edges": edges,
            "source": "start_end_params"
        }
    else:
        raise HTTPException(status_code=400, detail="Either provide start/end parameters or user_roadmap_path_id")
        
    # except HTTPException:
    #     raise
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Error finding skill path: {str(e)}")
