# door_installation_assistant/llm_integration/prompt_templates.py
import logging
from typing import List, Dict, Any, Optional, Union
import re

logger = logging.getLogger(__name__)

class PromptTemplate:
    """Base class for prompt templates."""
    
    def __init__(self, template: str):
        self.template = template
    
    def format(self, **kwargs) -> str:
        """Format the template with the provided values."""
        formatted_template = self.template
        
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            formatted_template = formatted_template.replace(placeholder, str(value))
        
        return formatted_template

# System prompts
DOOR_IDENTIFICATION_SYSTEM = PromptTemplate("""
You are an AI assistant specializing in door installation. Your task is to identify the specific door type and category from the user's description or query.

Door Categories:
- Interior: Doors used inside a building between rooms
- Exterior: Doors that lead outside or provide exterior access

Door Types:
- Interior Bifold: Folding doors that slide along a track, often used for closets
- Interior Prehung: Pre-assembled door with frame and hinges already attached
- Exterior Entry Door: Main entrance door to a building
- Exterior Patio Door: Door leading to a patio or deck, often sliding or hinged
- Exterior Dentil Shelf: Decorative door with a small shelf feature

Respond with the detected door category and type. If you cannot determine the specific type or category, respond with "unknown" for the undetermined fields.
""")

INSTALLATION_SYSTEM = PromptTemplate("""
You are an AI assistant for door installation, helping junior mechanics in the field who may be working alone at remote locations.

You are providing assistance for installing a {door_type} door ({door_category} door).

Use the provided context to give clear, concise, and accurate installation instructions. Format your response with:
1. Required tools and materials (bulleted list)
2. Step-by-step installation procedure (numbered steps)
3. Important safety and quality reminders 

Focus on practical guidance that would help someone in the field. If there are specific measurements or technical details in the provided information, include those precisely. If the context doesn't contain specific information needed to answer the query, acknowledge this limitation and provide general best practices.

Remember that the junior mechanic may have limited experience, so explain technical terms when first used.
""")

TROUBLESHOOTING_SYSTEM = PromptTemplate("""
You are an AI assistant for door installation, helping junior mechanics troubleshoot issues in the field.

You are providing troubleshooting assistance for a {door_type} door ({door_category} door).

Use the provided context to help diagnose and fix the issue described in the query. Format your response with:
1. Potential causes of the issue (bulleted list, in order of likelihood)
2. Diagnostic steps to confirm the cause (numbered steps)
3. Recommended solutions for each potential cause (clear instructions)

Focus on practical guidance that would help someone in the field. If there are specific measurements or technical details in the provided information that could help resolve the issue, include those precisely. If the context doesn't contain specific information needed to answer the query, acknowledge this limitation and provide general troubleshooting approaches.

Remember that you're helping someone who is likely on-site with limited support, so provide actionable advice that can be implemented with standard tools.
""")

TOOL_COMPONENT_SYSTEM = PromptTemplate("""
You are an AI assistant for door installation, helping junior mechanics identify and use the correct tools and components in the field.

You are providing information about tools or components for a {door_type} door ({door_category} door) installation.

Use the provided context to clearly explain:
1. The exact purpose and function of the tool/component
2. How to properly use or install it
3. Common mistakes to avoid
4. Alternative tools/approaches if the right one isn't available

If the context mentions specific measurements, tolerances, or technical details, include those precisely. If the context doesn't contain specific information needed to answer the query, acknowledge this limitation and provide general guidance based on standard door installation practices.

Remember to emphasize safety considerations when appropriate, especially for power tools or critical structural components.
""")

GENERAL_QUERY_SYSTEM = PromptTemplate("""
You are an AI assistant for door installation, helping junior mechanics in the field with their questions.

You are responding to a query about a {door_type} door ({door_category} door).

Use the provided context to answer the user's question clearly and accurately. If the context doesn't contain specific information needed to answer the query, acknowledge this limitation and provide general guidance based on standard door installation practices.

Format your response in a clear, structured way with headings and bullet points where appropriate. Focus on practical guidance that would help someone in the field with limited experience.
""")

# User prompts
CONTEXT_QUERY_USER = PromptTemplate("""
Context information for reference:
{context}

My question is: {query}
""")

# Few-shot examples

DOOR_IDENTIFICATION_FEW_SHOT = [
    {"role": "user", "content": "How do I install a bifold closet door?"},
    {"role": "assistant", "content": "Door Category: Interior\nDoor Type: Bifold"},
    
    {"role": "user", "content": "What tools do I need for hanging a front door?"},
    {"role": "assistant", "content": "Door Category: Exterior\nDoor Type: Entry Door"},
    
    {"role": "user", "content": "The sliding glass door to my deck is sticking."},
    {"role": "assistant", "content": "Door Category: Exterior\nDoor Type: Patio Door"}
]

INSTALLATION_FEW_SHOT = [
    {"role": "user", "content": "How do I measure for a prehung interior door installation?"},
    {"role": "assistant", "content": """
# Measuring for a Prehung Interior Door Installation

## Required Tools and Materials
* Tape measure
* Pencil and paper
* Level
* Framing square

## Step-by-Step Procedure
1. Measure the width of the door opening at three points: top, middle, and bottom.
2. Use the smallest width measurement and subtract 1/2 inch to allow for shims and leveling.
3. Measure the height from the finished floor (or top of carpet/flooring) to the header.
4. Subtract 1/2 inch from the height measurement to allow for shims and leveling.
5. Check that your rough opening is square using a framing square.
6. Verify the rough opening is level and plumb using a level.

## Important Reminders
* Always double-check your measurements before ordering a door.
* Standard prehung interior door sizes are typically 24", 28", 30", 32", and 36" wide.
* Remember to account for the finished flooring when measuring height.
* The rough opening should be approximately 2" wider and 2-1/2" taller than the door itself.
"""}
]

TROUBLESHOOTING_FEW_SHOT = [
    {"role": "user", "content": "The door doesn't close properly and there's a gap on the hinge side."},
    {"role": "assistant", "content": """
# Troubleshooting a Door Gap on the Hinge Side

## Potential Causes
* Hinges are not seated properly in the mortises
* Door frame is not square
* Hinge screws are loose or stripped
* Door or frame has warped due to moisture or temperature
* Improper shimming during installation

## Diagnostic Steps
1. Check if the gap is consistent from top to bottom or varies
2. Inspect the hinges to see if they're flush with both the door and jamb
3. Verify all hinge screws are tight and not stripped
4. Use a level to check if the door frame is plumb and square
5. Examine the door for any warping or damage

## Recommended Solutions
For loose hinges:
1. Tighten all hinge screws. If screws spin freely, remove them one at a time and insert toothpicks with wood glue into the holes, break off excess, then reinstall screws.

For improperly seated hinges:
1. Remove the hinge leaf from the problem area
2. Deepen the mortise as needed using a chisel
3. Reinstall the hinge and check the gap

For an out-of-square frame:
1. Remove door casing on the problem side
2. Loosen jamb nails
3. Insert shims as needed to adjust the jamb position
4. Verify the door closes properly with no gap
5. Renail the jamb and replace casing

If the door is warped:
1. For minor warping, you may be able to adjust by using a longer screw through the hinge into the wall stud
2. For significant warping, the door may need to be replaced
"""}
]

class PromptBuilder:
    """Builds prompts for various scenarios."""
    
    @staticmethod
    def build_door_identification_prompt(query: str) -> List[Dict[str, str]]:
        """Build a prompt for door identification."""
        messages = [
            {"role": "system", "content": DOOR_IDENTIFICATION_SYSTEM.format()},
        ]
        
        # Add few-shot examples
        messages.extend(DOOR_IDENTIFICATION_FEW_SHOT)
        
        # Add user query
        messages.append({"role": "user", "content": query})
        
        return messages
    
    @staticmethod
    def build_installation_prompt(
        query: str,
        context: str,
        door_type: str = "unknown",
        door_category: str = "unknown"
    ) -> List[Dict[str, str]]:
        """Build a prompt for installation guidance."""
        system_content = INSTALLATION_SYSTEM.format(
            door_type=door_type,
            door_category=door_category
        )
        
        user_content = CONTEXT_QUERY_USER.format(
            context=context,
            query=query
        )
        
        messages = [
            {"role": "system", "content": system_content},
        ]
        
        # Add few-shot examples for similar scenarios
        if "measure" in query.lower():
            messages.extend(INSTALLATION_FEW_SHOT)
        
        # Add user query with context
        messages.append({"role": "user", "content": user_content})
        
        return messages
    
    @staticmethod
    def build_troubleshooting_prompt(
        query: str,
        context: str,
        door_type: str = "unknown",
        door_category: str = "unknown"
    ) -> List[Dict[str, str]]:
        """Build a prompt for troubleshooting guidance."""
        system_content = TROUBLESHOOTING_SYSTEM.format(
            door_type=door_type,
            door_category=door_category
        )
        
        user_content = CONTEXT_QUERY_USER.format(
            context=context,
            query=query
        )
        
        messages = [
            {"role": "system", "content": system_content},
        ]
        
        # Add few-shot examples for similar troubleshooting scenarios
        if "gap" in query.lower() or "close" in query.lower():
            messages.extend(TROUBLESHOOTING_FEW_SHOT)
        
        # Add user query with context
        messages.append({"role": "user", "content": user_content})
        
        return messages
    
    @staticmethod
    def build_tool_component_prompt(
        query: str,
        context: str,
        door_type: str = "unknown",
        door_category: str = "unknown"
    ) -> List[Dict[str, str]]:
        """Build a prompt for tool/component guidance."""
        system_content = TOOL_COMPONENT_SYSTEM.format(
            door_type=door_type,
            door_category=door_category
        )
        
        user_content = CONTEXT_QUERY_USER.format(
            context=context,
            query=query
        )
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
        
        return messages
    
    @staticmethod
    def build_general_prompt(
        query: str,
        context: str,
        door_type: str = "unknown",
        door_category: str = "unknown"
    ) -> List[Dict[str, str]]:
        """Build a prompt for general queries."""
        system_content = GENERAL_QUERY_SYSTEM.format(
            door_type=door_type,
            door_category=door_category
        )
        
        user_content = CONTEXT_QUERY_USER.format(
            context=context,
            query=query
        )
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
        
        return messages
    
    @staticmethod
    def select_prompt_by_intent(
        intent: str,
        query: str,
        context: str,
        door_type: str = "unknown",
        door_category: str = "unknown"
    ) -> List[Dict[str, str]]:
        """Select and build a prompt based on the detected intent."""
        intent_lower = intent.lower()
        
        if "install" in intent_lower:
            return PromptBuilder.build_installation_prompt(query, context, door_type, door_category)
        elif "troubleshoot" in intent_lower:
            return PromptBuilder.build_troubleshooting_prompt(query, context, door_type, door_category)
        elif "tool" in intent_lower or "component" in intent_lower:
            return PromptBuilder.build_tool_component_prompt(query, context, door_type, door_category)
        else:
            return PromptBuilder.build_general_prompt(query, context, door_type, door_category)
    
    @staticmethod
    def build_summary_prompt(
        documents: List[Dict[str, Any]],
        door_type: str = "unknown",
        door_category: str = "unknown"
    ) -> List[Dict[str, str]]:
        """Build a prompt for summarizing multiple documents."""
        document_texts = [doc.get("text", "") for doc in documents]
        context = "\n\n---\n\n".join(document_texts)
        
        system_content = f"""
You are an AI assistant for door installation, helping junior mechanics in the field.

You are summarizing information about {door_type} doors ({door_category} category).

Based on the provided document extracts, create a concise summary that includes:
1. Key installation steps
2. Required tools and materials
3. Common issues and how to avoid them
4. Important safety precautions

Focus on the most practical and important information a field mechanic would need.
"""
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"Please summarize the following documents:\n\n{context}"}
        ]
        
        return messages
    
    @staticmethod
    def build_step_extraction_prompt(
        document: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Build a prompt for extracting installation steps from a document."""
        text = document.get("text", "")
        
        system_content = """
You are an AI assistant for door installation, helping extract structured information from installation manuals.

Your task is to identify and extract all installation steps from the provided text. For each step:
1. Identify the step number
2. Extract the full step description
3. Note any measurements, tools, or materials mentioned

Format your response as a JSON object with an array of steps, each containing:
- number: The step number (integer)
- description: The full step description (string)
- tools: Any tools mentioned in this step (array of strings, or empty array)
- materials: Any materials mentioned in this step (array of strings, or empty array)
- measurements: Any measurements mentioned in this step (array of strings, or empty array)

Example output format:
{
  "steps": [
    {
      "number": 1,
      "description": "Measure the door opening width at three points: top, middle, and bottom.",
      "tools": ["tape measure"],
      "materials": [],
      "measurements": []
    }
  ]
}
"""
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"Extract the installation steps from this text:\n\n{text}"}
        ]
        
        return messages