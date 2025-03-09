# door_installation_assistant/evaluation/synthetic_scenarios.py
import logging
import json
import random
from typing import Dict, Any, List, Optional
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class ScenarioGenerator:
    """Generates synthetic test scenarios for evaluation."""
    
    def __init__(self, scenarios_path: Optional[str] = None):
        """
        Initialize the scenario generator.
        
        Args:
            scenarios_path: Path to scenario template file.
        """
        self.scenarios_path = scenarios_path
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Any]:
        """
        Load scenario templates from file or use defaults.
        
        Returns:
            Dictionary with scenario templates.
        """
        try:
            if self.scenarios_path and os.path.exists(self.scenarios_path):
                with open(self.scenarios_path, 'r') as f:
                    return json.load(f)
            else:
                # Use default templates
                return {
                    "installation": self._get_installation_templates(),
                    "troubleshooting": self._get_troubleshooting_templates(),
                    "tools": self._get_tool_templates(),
                    "safety": self._get_safety_templates()
                }
        except Exception as e:
            logger.error(f"Error loading scenario templates: {str(e)}")
            return {
                "installation": self._get_installation_templates(),
                "troubleshooting": self._get_troubleshooting_templates(),
                "tools": self._get_tool_templates(),
                "safety": self._get_safety_templates()
            }
    
    def _get_installation_templates(self) -> List[Dict[str, Any]]:
        """
        Get installation scenario templates.
        
        Returns:
            List of installation scenario templates.
        """
        return [
            {
                "query_template": "How do I install a {door_type} door?",
                "expected_keywords": ["step", "measure", "level", "plumb", "square", "shim"],
                "category": "installation",
                "difficulty": "basic"
            },
            {
                "query_template": "What's the proper way to measure for a {door_type} door installation?",
                "expected_keywords": ["measure", "width", "height", "opening", "dimensions"],
                "category": "installation",
                "difficulty": "basic"
            },
            {
                "query_template": "I'm having trouble with the rough opening for my {door_type} door. It seems too small. What should I do?",
                "expected_keywords": ["rough opening", "dimension", "enlarge", "frame", "stud"],
                "category": "installation",
                "difficulty": "intermediate"
            },
            {
                "query_template": "How do I make sure my {door_type} door is level and plumb during installation?",
                "expected_keywords": ["level", "plumb", "square", "shim", "adjust"],
                "category": "installation",
                "difficulty": "intermediate"
            },
            {
                "query_template": "What's the correct order of steps for installing a {door_type} door from start to finish?",
                "expected_keywords": ["step", "measure", "prepare", "position", "secure", "check"],
                "category": "installation",
                "difficulty": "advanced"
            }
        ]
    
    def _get_troubleshooting_templates(self) -> List[Dict[str, Any]]:
        """
        Get troubleshooting scenario templates.
        
        Returns:
            List of troubleshooting scenario templates.
        """
        return [
            {
                "query_template": "My {door_type} door won't close properly. There's a gap at the top. How do I fix it?",
                "expected_keywords": ["hinge", "sagging", "shim", "adjust", "level"],
                "category": "troubleshooting",
                "difficulty": "basic"
            },
            {
                "query_template": "The {door_type} door is sticking and hard to open/close. What could be causing this?",
                "expected_keywords": ["humidity", "warping", "hinge", "rubbing", "alignment"],
                "category": "troubleshooting",
                "difficulty": "basic"
            },
            {
                "query_template": "There's a large gap between my {door_type} door and the frame on the latch side. How can I fix this?",
                "expected_keywords": ["shim", "adjust", "hinge", "strike plate", "reposition"],
                "category": "troubleshooting",
                "difficulty": "intermediate"
            },
            {
                "query_template": "My newly installed {door_type} door is making a loud squeaking noise when opening. What should I do?",
                "expected_keywords": ["hinge", "lubricate", "loose", "tighten", "pins"],
                "category": "troubleshooting",
                "difficulty": "basic"
            },
            {
                "query_template": "I think I installed my {door_type} door upside down. Is there any way to tell for sure, and how can I fix it?",
                "expected_keywords": ["orientation", "hinge", "remove", "reinstall", "mortise"],
                "category": "troubleshooting",
                "difficulty": "advanced"
            }
        ]
    
    def _get_tool_templates(self) -> List[Dict[str, Any]]:
        """
        Get tool scenario templates.
        
        Returns:
            List of tool scenario templates.
        """
        return [
            {
                "query_template": "What tools do I need to install a {door_type} door?",
                "expected_keywords": ["hammer", "level", "drill", "screwdriver", "tape measure"],
                "category": "tools",
                "difficulty": "basic"
            },
            {
                "query_template": "I don't have a power drill. Can I still install a {door_type} door?",
                "expected_keywords": ["manual", "screwdriver", "hand tools", "alternative", "pre-drill"],
                "category": "tools",
                "difficulty": "intermediate"
            },
            {
                "query_template": "What's the best tool for cutting the bottom of a {door_type} door to fit over carpet?",
                "expected_keywords": ["circular saw", "handsaw", "jigsaw", "plane", "guide"],
                "category": "tools",
                "difficulty": "intermediate"
            },
            {
                "query_template": "How do I use a router to mortise hinges for a {door_type} door?",
                "expected_keywords": ["router", "template", "depth", "bit", "secure"],
                "category": "tools",
                "difficulty": "advanced"
            },
            {
                "query_template": "What specialized tools might make {door_type} door installation easier?",
                "expected_keywords": ["door jack", "hinge jig", "door dolly", "laser level", "specialized"],
                "category": "tools",
                "difficulty": "advanced"
            }
        ]
    
    def _get_safety_templates(self) -> List[Dict[str, Any]]:
        """
        Get safety scenario templates.
        
        Returns:
            List of safety scenario templates.
        """
        return [
            {
                "query_template": "What safety precautions should I take when installing a {door_type} door?",
                "expected_keywords": ["gloves", "goggles", "mask", "lifting", "partner"],
                "category": "safety",
                "difficulty": "basic"
            },
            {
                "query_template": "Is it safe to install a {door_type} door by myself, or do I need help?",
                "expected_keywords": ["weight", "assistance", "partner", "support", "door jack"],
                "category": "safety",
                "difficulty": "basic"
            },
            {
                "query_template": "What's the safe way to handle and transport a heavy {door_type} door?",
                "expected_keywords": ["lift", "back", "dolly", "partner", "technique"],
                "category": "safety",
                "difficulty": "intermediate"
            },
            {
                "query_template": "What PPE should I wear when installing a {door_type} door?",
                "expected_keywords": ["gloves", "goggles", "mask", "boots", "protection"],
                "category": "safety",
                "difficulty": "basic"
            },
            {
                "query_template": "Are there any electrical safety concerns when installing a {door_type} door near wiring?",
                "expected_keywords": ["circuit", "breaker", "stud finder", "wiring", "drill"],
                "category": "safety",
                "difficulty": "advanced"
            }
        ]
    
    def generate_scenarios(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        door_types: Optional[List[str]] = None,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate synthetic test scenarios.
        
        Args:
            category: Scenario category (installation, troubleshooting, tools, safety).
            difficulty: Scenario difficulty (basic, intermediate, advanced).
            door_types: List of door types to include.
            count: Number of scenarios to generate.
            
        Returns:
            List of generated scenarios.
        """
        try:
            # Default door types if not provided
            if not door_types:
                door_types = [
                    "interior prehung", "bifold", "exterior entry", "patio", "dentil shelf"
                ]
            
            # Filter templates by category and difficulty
            filtered_templates = []
            for cat, templates in self.templates.items():
                if category and cat != category:
                    continue
                
                for template in templates:
                    if difficulty and template["difficulty"] != difficulty:
                        continue
                    
                    filtered_templates.append(template)
            
            # Generate scenarios
            scenarios = []
            for _ in range(count):
                # Select random template and door type
                template = random.choice(filtered_templates) if filtered_templates else random.choice(
                    [t for cat_templates in self.templates.values() for t in cat_templates]
                )
                door_type = random.choice(door_types)
                
                # Generate query
                query = template["query_template"].format(door_type=door_type)
                
                # Create scenario
                scenario = {
                    "query": query,
                    "door_type": door_type,
                    "category": template["category"],
                    "difficulty": template["difficulty"],
                    "expected_keywords": template["expected_keywords"]
                }
                
                scenarios.append(scenario)
            
            return scenarios
        
        except Exception as e:
            logger.error(f"Error generating scenarios: {str(e)}")
            return []
    
    def save_scenarios(self, scenarios: List[Dict[str, Any]], output_path: str) -> bool:
        """
        Save generated scenarios to a file.
        
        Args:
            scenarios: List of generated scenarios.
            output_path: Path to save scenarios.
            
        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(scenarios, f, indent=2)
            
            logger.info(f"Saved {len(scenarios)} scenarios to {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving scenarios: {str(e)}")
            return False
    
    def load_scenarios(self, input_path: str) -> List[Dict[str, Any]]:
        """
        Load scenarios from a file.
        
        Args:
            input_path: Path to load scenarios from.
            
        Returns:
            List of loaded scenarios.
        """
        try:
            with open(input_path, 'r') as f:
                scenarios = json.load(f)
            
            logger.info(f"Loaded {len(scenarios)} scenarios from {input_path}")
            return scenarios
        
        except Exception as e:
            logger.error(f"Error loading scenarios: {str(e)}")
            return []
    
    def generate_evaluation_dataset(
        self,
        output_path: Optional[str] = None,
        categories: Optional[List[str]] = None,
        difficulties: Optional[List[str]] = None,
        door_types: Optional[List[str]] = None,
        total_count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Generate a comprehensive evaluation dataset.
        
        Args:
            output_path: Path to save dataset.
            categories: List of categories to include.
            difficulties: List of difficulties to include.
            door_types: List of door types to include.
            total_count: Total number of scenarios to generate.
            
        Returns:
            List of generated scenarios.
        """
        try:
            # Default categories and difficulties if not provided
            if not categories:
                categories = ["installation", "troubleshooting", "tools", "safety"]
            
            if not difficulties:
                difficulties = ["basic", "intermediate", "advanced"]
            
            # Calculate counts per category
            counts = {}
            base_count = total_count // len(categories)
            remainder = total_count % len(categories)
            
            for i, category in enumerate(categories):
                counts[category] = base_count + (1 if i < remainder else 0)
            
            # Generate scenarios for each category
            all_scenarios = []
            for category, count in counts.items():
                category_scenarios = self.generate_scenarios(
                    category=category,
                    door_types=door_types,
                    count=count
                )
                all_scenarios.extend(category_scenarios)
            
            # Shuffle scenarios
            random.shuffle(all_scenarios)
            
            # Save scenarios if output path provided
            if output_path:
                self.save_scenarios(all_scenarios, output_path)
            
            return all_scenarios
        
        except Exception as e:
            logger.error(f"Error generating evaluation dataset: {str(e)}")
            return []