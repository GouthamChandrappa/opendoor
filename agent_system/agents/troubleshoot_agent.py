# door_installation_assistant/agent_system/agents/troubleshoot_agent.py
import logging
from typing import Dict, Any, List, Optional, Tuple
import re

from .base_agent import Agent
from ...llm_integration.prompt_templates import PromptBuilder
from ...llm_integration.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)

class TroubleshootAgent(Agent):
    """Agent for troubleshooting door installation issues."""
    
    @property
    def agent_type(self) -> str:
        return "troubleshooting"
    
    @property
    def description(self) -> str:
        return "Troubleshoots door installation and operation issues"
    
    def process(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Process a query to provide troubleshooting assistance.
        
        Args:
            query: User query.
            **kwargs: Additional arguments including door type and category.
            
        Returns:
            Dictionary with troubleshooting solution and relevant information.
        """
        try:
            # Extract door information from kwargs
            door_category = kwargs.get("door_category", "unknown")
            door_type = kwargs.get("door_type", "unknown")
            
            # Extract issue from query
            issue = self._extract_issue(query)
            
            # Create filter for document retrieval
            filter_dict = {}
            if door_category != "unknown":
                filter_dict["door_category"] = door_category
            if door_type != "unknown":
                filter_dict["door_type"] = door_type
            
            # Retrieve relevant documents
            documents = self._retrieve_documents(
                query=issue,
                filter_dict=filter_dict,
                top_k=5
            )
            
            # Format documents as context
            context = self._format_documents_as_context(documents)
            
            # Build prompt for troubleshooting
            messages = PromptBuilder.build_troubleshooting_prompt(
                query=query,
                context=context,
                door_type=door_type,
                door_category=door_category
            )
            
            # Generate response
            response = self._generate_response(messages, temperature=0.3)
            
            # Format response to extract structured information
            formatted_response = ResponseFormatter.format_troubleshooting(response)
            
            # Extract common issues from response
            issues = self._extract_issues_from_response(formatted_response)
            
            # Return the troubleshooting information
            return {
                "solution": response,
                "issues": issues,
                "causes": formatted_response.get("causes", []),
                "problem_description": formatted_response.get("problem_description", ""),
                "door_category": door_category,
                "door_type": door_type,
                "document_count": len(documents)
            }
        
        except Exception as e:
            logger.error(f"Error providing troubleshooting solution: {str(e)}")
            return {
                "solution": "I'm sorry, I encountered an error while generating a troubleshooting solution. Please try again with a more specific description of the issue.",
                "issues": [],
                "causes": [],
                "problem_description": "",
                "door_category": kwargs.get("door_category", "unknown"),
                "door_type": kwargs.get("door_type", "unknown"),
                "error": str(e)
            }
    
    def _extract_issue(self, query: str) -> str:
        """
        Extract the main issue from a troubleshooting query.
        
        Args:
            query: User query.
            
        Returns:
            Extracted issue.
        """
        # Look for common issue patterns
        issue_patterns = [
            r"(door (?:won't|doesn't|isn't) (?:close|open|latch|lock|align|fit))",
            r"(gap(?:s)? (?:between|in|around) (?:the )?door)",
            r"(door (?:is )?(?:stuck|jammed|binding|rubbing|dragging|sagging|warped))",
            r"(hinge(?:s)? (?:is|are) (?:loose|squeaking|broken|damaged))",
            r"(knob|handle|lock (?:is )?(?:loose|stuck|broken|not working))"
        ]
        
        for pattern in issue_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # If no specific pattern matches, return the whole query
        return query
    
    def _extract_issues_from_response(self, formatted_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract structured issues from a formatted response.
        
        Args:
            formatted_response: Formatted response from ResponseFormatter.
            
        Returns:
            List of structured issues.
        """
        issues = []
        
        # Extract issues from causes and solutions
        causes = formatted_response.get("causes", [])
        solutions = formatted_response.get("solutions", [])
        
        for i, cause in enumerate(causes):
            issue = {
                "issue": cause,
                "solution": ""
            }
            
            # Try to find a matching solution
            if i < len(solutions):
                solution = solutions[i]
                if isinstance(solution, dict):
                    issue["solution"] = solution.get("solution", "")
                else:
                    issue["solution"] = solution
            
            issues.append(issue)
        
        return issues
    
    def get_common_issues(self, door_category: str, door_type: str) -> Dict[str, Any]:
        """
        Get common issues for a specific door type.
        
        Args:
            door_category: Door category.
            door_type: Door type.
            
        Returns:
            Dictionary with common issues and solutions.
        """
        try:
            # Create filter for document retrieval
            filter_dict = {}
            
            if door_category != "unknown":
                filter_dict["door_category"] = door_category
            if door_type != "unknown":
                filter_dict["door_type"] = door_type
            
            # Retrieve relevant documents
            documents = self._retrieve_documents(
                query=f"common problems with {door_type} {door_category} door",
                filter_dict=filter_dict,
                top_k=5
            )
            
            # Format documents as context
            context = self._format_documents_as_context(documents)
            
            # Build prompt for common issues
            messages = PromptBuilder.build_troubleshooting_prompt(
                query=f"What are the most common issues with {door_type} doors and how do I fix them?",
                context=context,
                door_type=door_type,
                door_category=door_category
            )
            
            # Generate response
            response = self._generate_response(messages, temperature=0.3)
            
            # Format response to extract structured information
            formatted_response = ResponseFormatter.format_troubleshooting(response)
            
            # Extract issues from response
            issues = self._extract_issues_from_response(formatted_response)
            
            return {
                "common_issues": issues,
                "raw_response": response,
                "found": len(documents) > 0
            }
        
        except Exception as e:
            logger.error(f"Error retrieving common issues: {str(e)}")
            return {
                "common_issues": [],
                "raw_response": f"Error retrieving common issues: {str(e)}",
                "found": False,
                "error": str(e)
            }
    
    def diagnose_issue(self, issue_description: str, door_category: str, door_type: str) -> Dict[str, Any]:
        """
        Diagnose a specific door issue.
        
        Args:
            issue_description: Description of the issue.
            door_category: Door category.
            door_type: Door type.
            
        Returns:
            Dictionary with diagnosis and solutions.
        """
        try:
            # Create filter for document retrieval
            filter_dict = {}
            
            if door_category != "unknown":
                filter_dict["door_category"] = door_category
            if door_type != "unknown":
                filter_dict["door_type"] = door_type
            
            # Extract main keywords from issue description
            issue_keywords = self._extract_issue(issue_description)
            
            # Retrieve relevant documents
            documents = self._retrieve_documents(
                query=issue_keywords,
                filter_dict=filter_dict,
                top_k=5
            )
            
            # Format documents as context
            context = self._format_documents_as_context(documents)
            
            # Build prompt for diagnosis
            messages = PromptBuilder.build_troubleshooting_prompt(
                query=f"I'm having this issue with my {door_type} door: {issue_description}. What could be causing it and how do I fix it?",
                context=context,
                door_type=door_type,
                door_category=door_category
            )
            
            # Generate response
            response = self._generate_response(messages, temperature=0.3)
            
            # Format response to extract structured information
            formatted_response = ResponseFormatter.format_troubleshooting(response)
            
            return {
                "diagnosis": formatted_response.get("problem_description", ""),
                "causes": formatted_response.get("causes", []),
                "solutions": formatted_response.get("solutions", []),
                "raw_response": response,
                "found": len(documents) > 0
            }
        
        except Exception as e:
            logger.error(f"Error diagnosing issue: {str(e)}")
            return {
                "diagnosis": "Unable to diagnose the issue.",
                "causes": [],
                "solutions": [],
                "raw_response": f"Error diagnosing issue: {str(e)}",
                "found": False,
                "error": str(e)
            }