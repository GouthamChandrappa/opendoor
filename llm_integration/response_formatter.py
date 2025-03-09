# door_installation_assistant/llm_integration/response_formatter.py
import re
import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """Formats LLM responses for different use cases."""
    
    @staticmethod
    def format_installation_steps(response: str) -> Dict[str, Any]:
        """
        Format installation steps from an LLM response.
        
        Args:
            response: LLM response text.
            
        Returns:
            Dictionary with formatted installation steps.
        """
        # Extract sections from the response
        sections = ResponseFormatter._extract_sections(response)
        
        # Extract steps
        steps = ResponseFormatter._extract_steps(response)
        
        # Extract tools and materials
        tools_materials = ResponseFormatter._extract_tools_materials(response)
        
        # Extract safety information
        safety_info = ResponseFormatter._extract_safety_info(response)
        
        return {
            "sections": sections,
            "steps": steps,
            "tools_materials": tools_materials,
            "safety_info": safety_info,
            "raw_response": response
        }
    
    @staticmethod
    def format_troubleshooting(response: str) -> Dict[str, Any]:
        """
        Format troubleshooting guidance from an LLM response.
        
        Args:
            response: LLM response text.
            
        Returns:
            Dictionary with formatted troubleshooting guidance.
        """
        # Extract problem description
        problem_description = ResponseFormatter._extract_problem_description(response)
        
        # Extract potential causes
        causes = ResponseFormatter._extract_causes(response)
        
        # Extract solutions
        solutions = ResponseFormatter._extract_solutions(response)
        
        return {
            "problem_description": problem_description,
            "causes": causes,
            "solutions": solutions,
            "raw_response": response
        }
    
    @staticmethod
    def format_tool_recommendations(response: str) -> Dict[str, Any]:
        """
        Format tool recommendations from an LLM response.
        
        Args:
            response: LLM response text.
            
        Returns:
            Dictionary with formatted tool recommendations.
        """
        # Extract recommended tools
        tools = ResponseFormatter._extract_recommended_tools(response)
        
        # Extract usage instructions
        usage = ResponseFormatter._extract_usage_instructions(response)
        
        # Extract alternatives
        alternatives = ResponseFormatter._extract_alternatives(response)
        
        return {
            "tools": tools,
            "usage": usage,
            "alternatives": alternatives,
            "raw_response": response
        }
    
    @staticmethod
    def format_for_chat(response: str) -> str:
        """
        Format a response for chat display.
        
        Args:
            response: LLM response text.
            
        Returns:
            Formatted response for chat display.
        """
        # Enhance headings
        response = ResponseFormatter._enhance_headings(response)
        
        # Format lists
        response = ResponseFormatter._enhance_lists(response)
        
        # Enhance step numbers
        response = ResponseFormatter._enhance_steps(response)
        
        # Highlight important warnings and tips
        response = ResponseFormatter._highlight_important_info(response)
        
        return response
    
    @staticmethod
    def format_for_mobile(response: str) -> str:
        """
        Format a response for mobile display (more concise).
        
        Args:
            response: LLM response text.
            
        Returns:
            Formatted response for mobile display.
        """
        # Convert long paragraphs to bullet points
        response = ResponseFormatter._paragraphs_to_bullets(response)
        
        # Remove verbose language
        response = ResponseFormatter._remove_verbosity(response)
        
        # Format for a smaller screen
        response = ResponseFormatter._format_for_small_screen(response)
        
        return response
    
    @staticmethod
    def extract_json(response: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from a response string.
        
        Args:
            response: Response string that might contain JSON.
            
        Returns:
            Extracted JSON as a dictionary, or None if no valid JSON found.
        """
        import json
        
        # Try to find JSON in the response using regex
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON between brackets
            json_match = re.search(r'({[\s\S]*})', response)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Response might be direct JSON
                json_str = response
        
        try:
            result = json.loads(json_str)
            return result
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from response")
            return None
    
    # Private helper methods
    
    @staticmethod
    def _extract_sections(text: str) -> List[Dict[str, str]]:
        """Extract sections from text based on headings."""
        sections = []
        
        # Find headings and their content
        heading_pattern = r'#{1,3}\s+(.+?)\n([\s\S]*?)(?=#{1,3}|\Z)'
        matches = re.finditer(heading_pattern, text)
        
        for match in matches:
            heading = match.group(1).strip()
            content = match.group(2).strip()
            sections.append({
                "heading": heading,
                "content": content
            })
        
        # If no headings found using markdown, try alternative patterns
        if not sections:
            # Look for uppercase lines that might be headings
            lines = text.split('\n')
            current_heading = None
            current_content = []
            
            for line in lines:
                stripped_line = line.strip()
                if stripped_line and stripped_line.isupper():
                    # If we have a previous heading, add it
                    if current_heading:
                        sections.append({
                            "heading": current_heading,
                            "content": '\n'.join(current_content)
                        })
                    current_heading = stripped_line
                    current_content = []
                elif current_heading:
                    current_content.append(line)
            
            # Add the last section
            if current_heading:
                sections.append({
                    "heading": current_heading,
                    "content": '\n'.join(current_content)
                })
        
        return sections
    
    @staticmethod
    def _extract_steps(text: str) -> List[Dict[str, Any]]:
        """Extract numbered steps from text."""
        steps = []
        
        # Look for numbered steps (e.g., "1. ", "Step 1:", etc.)
        step_patterns = [
            r'(\d+)\.\s+([\s\S]*?)(?=\d+\.\s+|\Z)',            # 1. Step description
            r'Step\s+(\d+)[:\)]\s+([\s\S]*?)(?=Step\s+\d+|$)'  # Step 1: Step description
        ]
        
        for pattern in step_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                step_number = int(match.group(1))
                step_text = match.group(2).strip()
                steps.append({
                    "number": step_number,
                    "description": step_text
                })
            
            if steps:
                break  # Stop after finding steps with the first pattern
        
        # Sort steps by number
        steps.sort(key=lambda x: x["number"])
        
        return steps
    
    @staticmethod
    def _extract_tools_materials(text: str) -> List[str]:
        """Extract tools and materials from text."""
        tools_materials = []
        
        # Look for tools/materials section
        section_patterns = [
            r'(?:Tools|Materials|Tools and Materials|Required Tools|You will need)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)',
            r'(?:Tools Required|Materials Required)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)'
        ]
        
        for pattern in section_patterns:
            section_match = re.search(pattern, text, re.IGNORECASE)
            if section_match:
                section_text = section_match.group(1).strip()
                
                # Extract bullet or numbered items
                item_matches = re.finditer(r'(?:^|\n)(?:[*\-•]|\d+\.)\s+(.*?)(?=\n[*\-•]|\n\d+\.|\Z)', section_text)
                for item_match in item_matches:
                    tools_materials.append(item_match.group(1).strip())
                
                # If no bullet points found, split by newlines
                if not tools_materials:
                    items = [line.strip() for line in section_text.split('\n') if line.strip()]
                    tools_materials.extend(items)
                
                break
        
        return tools_materials
    
    @staticmethod
    def _extract_safety_info(text: str) -> List[str]:
        """Extract safety information from text."""
        safety_info = []
        
        # Look for safety section
        safety_section_patterns = [
            r'(?:Safety|Safety Information|Safety Considerations|Important Safety|Precautions)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)',
            r'(?:Warning|Caution|Safety Warning)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)'
        ]
        
        for pattern in safety_section_patterns:
            section_match = re.search(pattern, text, re.IGNORECASE)
            if section_match:
                section_text = section_match.group(1).strip()
                
                # Extract bullet or numbered items
                item_matches = re.finditer(r'(?:^|\n)(?:[*\-•]|\d+\.)\s+(.*?)(?=\n[*\-•]|\n\d+\.|\Z)', section_text)
                for item_match in item_matches:
                    safety_info.append(item_match.group(1).strip())
                
                # If no bullet points found, split by newlines
                if not safety_info:
                    items = [line.strip() for line in section_text.split('\n') if line.strip()]
                    safety_info.extend(items)
                
                break
        
        # If no safety section found, search for safety warnings throughout the text
        if not safety_info:
            warning_matches = re.finditer(r'(Warning|Caution|IMPORTANT|NOTE|SAFETY TIP):\s+(.*?)(?=\n|$)', text, re.IGNORECASE)
            for match in warning_matches:
                warning_type = match.group(1).strip()
                warning_text = match.group(2).strip()
                safety_info.append(f"{warning_type}: {warning_text}")
        
        return safety_info
    
    @staticmethod
    def _extract_problem_description(text: str) -> str:
        """Extract problem description from troubleshooting text."""
        # Look for problem description section
        section_patterns = [
            r'(?:Problem|Issue|Symptom)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)',
            r'(?:Problem Description|Issue Description)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)'
        ]
        
        for pattern in section_patterns:
            section_match = re.search(pattern, text, re.IGNORECASE)
            if section_match:
                return section_match.group(1).strip()
        
        # If no specific section found, return first paragraph
        paragraphs = text.split('\n\n')
        if paragraphs:
            return paragraphs[0].strip()
        
        return ""
    
    @staticmethod
    def _extract_causes(text: str) -> List[str]:
        """Extract potential causes from troubleshooting text."""
        causes = []
        
        # Look for causes section
        section_patterns = [
            r'(?:Causes|Potential Causes|Possible Causes)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)',
            r'(?:Why this happens|Root cause)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)'
        ]
        
        for pattern in section_patterns:
            section_match = re.search(pattern, text, re.IGNORECASE)
            if section_match:
                section_text = section_match.group(1).strip()
                
                # Extract bullet or numbered items
                item_matches = re.finditer(r'(?:^|\n)(?:[*\-•]|\d+\.)\s+(.*?)(?=\n[*\-•]|\n\d+\.|\Z)', section_text)
                for item_match in item_matches:
                    causes.append(item_match.group(1).strip())
                
                # If no bullet points found, split by newlines
                if not causes:
                    items = [line.strip() for line in section_text.split('\n') if line.strip()]
                    causes.extend(items)
                
                break
        
        return causes
    
    @staticmethod
    def _extract_solutions(text: str) -> List[Dict[str, str]]:
        """Extract solutions from troubleshooting text."""
        solutions = []
        
        # Look for solutions section
        section_patterns = [
            r'(?:Solutions|Fixes|Resolution|How to Fix)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)',
            r'(?:Troubleshooting Steps|Repair Steps)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)'
        ]
        
        for pattern in section_patterns:
            section_match = re.search(pattern, text, re.IGNORECASE)
            if section_match:
                section_text = section_match.group(1).strip()
                
                # Extract numbered solutions with steps
                solution_matches = re.finditer(r'(?:^|\n)(?:(\d+)\.|\*|\-|•)\s+(.*?)(?=\n(?:\d+\.|\*|\-|•)|\Z)', section_text)
                for solution_match in solution_matches:
                    number = solution_match.group(1) if solution_match.group(1) else ""
                    solution_text = solution_match.group(2).strip()
                    solutions.append({
                        "number": number,
                        "solution": solution_text
                    })
                
                # If no bullet points found and text isn't empty, use the whole section
                if not solutions and section_text:
                    solutions.append({
                        "number": "",
                        "solution": section_text
                    })
                
                break
        
        return solutions
    
    @staticmethod
    def _extract_recommended_tools(text: str) -> List[Dict[str, str]]:
        """Extract recommended tools from text."""
        tools = []
        
        # Look for tools section
        section_patterns = [
            r'(?:Recommended Tools|Required Tools|Tools Needed)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)',
            r'(?:Tools|Equipment)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)'
        ]
        
        for pattern in section_patterns:
            section_match = re.search(pattern, text, re.IGNORECASE)
            if section_match:
                section_text = section_match.group(1).strip()
                
                # Extract tool items with possible descriptions
                tool_matches = re.finditer(r'(?:^|\n)(?:[*\-•]|\d+\.)\s+(.*?)(?=\n[*\-•]|\n\d+\.|\Z)', section_text)
                for tool_match in tool_matches:
                    tool_text = tool_match.group(1).strip()
                    
                    # Try to separate tool name from description
                    tool_parts = tool_text.split(":", 1)
                    if len(tool_parts) > 1:
                        tool_name = tool_parts[0].strip()
                        tool_description = tool_parts[1].strip()
                    else:
                        # Try splitting on "-" or "–"
                        tool_parts = re.split(r'\s+[-–]\s+', tool_text, 1)
                        if len(tool_parts) > 1:
                            tool_name = tool_parts[0].strip()
                            tool_description = tool_parts[1].strip()
                        else:
                            tool_name = tool_text
                            tool_description = ""
                    
                    tools.append({
                        "name": tool_name,
                        "description": tool_description
                    })
                
                # If no bullet points found, split by newlines
                if not tools:
                    items = [line.strip() for line in section_text.split('\n') if line.strip()]
                    for item in items:
                        tools.append({
                            "name": item,
                            "description": ""
                        })
                
                break
        
        return tools
    
    @staticmethod
    def _extract_usage_instructions(text: str) -> str:
        """Extract usage instructions from text."""
        # Look for usage instructions section
        section_patterns = [
            r'(?:Usage|Usage Instructions|How to Use|Instructions)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)',
            r'(?:Using the Tool|Tool Usage)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)'
        ]
        
        for pattern in section_patterns:
            section_match = re.search(pattern, text, re.IGNORECASE)
            if section_match:
                return section_match.group(1).strip()
        
        return ""
    
    @staticmethod
    def _extract_alternatives(text: str) -> List[str]:
        """Extract alternative tools or methods from text."""
        alternatives = []
        
        # Look for alternatives section
        section_patterns = [
            r'(?:Alternatives|Alternative Tools|Other Options)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)',
            r'(?:If you don\'t have|Substitutes)[:\n]([\s\S]*?)(?=\n\n|\n#|\Z)'
        ]
        
        for pattern in section_patterns:
            section_match = re.search(pattern, text, re.IGNORECASE)
            if section_match:
                section_text = section_match.group(1).strip()
                
                # Extract bullet or numbered items
                item_matches = re.finditer(r'(?:^|\n)(?:[*\-•]|\d+\.)\s+(.*?)(?=\n[*\-•]|\n\d+\.|\Z)', section_text)
                for item_match in item_matches:
                    alternatives.append(item_match.group(1).strip())
                
                # If no bullet points found, split by newlines
                if not alternatives:
                    items = [line.strip() for line in section_text.split('\n') if line.strip()]
                    alternatives.extend(items)
                
                break
        
        return alternatives
    
    @staticmethod
    def _enhance_headings(text: str) -> str:
        """Enhance markdown headings for better visibility."""
        # Add spacing around headings and make them more prominent
        text = re.sub(r'(#{1,3})\s+(.+?)(\n|$)', r'\n\1 \2\3', text)
        return text
    
    @staticmethod
    def _enhance_lists(text: str) -> str:
        """Enhance markdown lists for better visibility."""
        # Make bullet lists use consistent bullets
        text = re.sub(r'^[ \t]*[-*][ \t]+', r'• ', text, flags=re.MULTILINE)
        return text
    
    @staticmethod
    def _enhance_steps(text: str) -> str:
        """Enhance step numbers for better visibility."""
        # Make step numbers more prominent
        text = re.sub(r'(Step\s+\d+[:.)])', r'**\1**', text)
        text = re.sub(r'^(\d+)\.\s+', r'**\1.** ', text, flags=re.MULTILINE)
        return text
    
    @staticmethod
    def _highlight_important_info(text: str) -> str:
        """Highlight important warnings and tips."""
        # Highlight warnings, cautions, and important notes
        text = re.sub(r'(Warning|Caution|IMPORTANT|NOTE|SAFETY TIP):\s+', r'**\1:** ', text, flags=re.IGNORECASE)
        
        # Add emoji to warnings and safety tips
        text = re.sub(r'(?i)warning:', r'⚠️ **WARNING:**', text)
        text = re.sub(r'(?i)caution:', r'🚨 **CAUTION:**', text)
        text = re.sub(r'(?i)safety tip:', r'🛡️ **SAFETY TIP:**', text)
        text = re.sub(r'(?i)important:', r'📢 **IMPORTANT:**', text)
        
        return text
    
    @staticmethod
    def _paragraphs_to_bullets(text: str) -> str:
        """Convert long paragraphs to bullet points for mobile view."""
        # Only convert paragraphs that are longer than 100 characters
        def replace_long_paragraph(match):
            paragraph = match.group(0)
            if len(paragraph) > 100 and paragraph.count('.') > 1:
                # Split into sentences
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                # Convert to bullets
                return '\n'.join([f"• {sentence}" for sentence in sentences if sentence.strip()])
            return paragraph
        
        # Find paragraphs (text between blank lines that's not already a list)
        text = re.sub(r'(?<!\n\s*[-•*])[^\n]+(?:\n(?!\n)[^\n]+)*', replace_long_paragraph, text)
        return text
    
    @staticmethod
    def _remove_verbosity(text: str) -> str:
        """Remove verbose language for a more concise response."""
        # Remove filler phrases
        verbose_phrases = [
            r"It's important to note that ",
            r"Please be aware that ",
            r"I would recommend that ",
            r"It should be mentioned that ",
            r"Don't forget that ",
            r"Keep in mind that ",
            r"As a general rule, ",
            r"Generally speaking, "
        ]
        
        for phrase in verbose_phrases:
            text = re.sub(phrase, "", text, flags=re.IGNORECASE)
        
        return text
    
    @staticmethod
    def _format_for_small_screen(text: str) -> str:
        """Format text for small screens."""
        # Reduce heading levels (# -> ##)
        text = re.sub(r'^#\s+', r'## ', text, flags=re.MULTILINE)
        
        # Break long lines
        text = re.sub(r'(.{50,70})\s+', r'\1\n', text)
        
        return text