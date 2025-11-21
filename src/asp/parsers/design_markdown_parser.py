"""
Markdown parser for Design Agent output.

This module parses markdown-formatted DesignSpecification documents into
structured data for Pydantic validation. Used by Design Agent v2 with
markdown output format.

Author: ASP Development Team
Date: November 21, 2025
"""

import json
import re
from datetime import datetime
from typing import Any, Optional


class DesignMarkdownParser:
    """
    Parser for Design Agent markdown output.

    Converts markdown-formatted DesignSpecification into a dictionary
    that can be validated by the DesignSpecification Pydantic model.

    Usage:
        parser = DesignMarkdownParser()
        design_dict = parser.parse(markdown_content)
        design_spec = DesignSpecification.model_validate(design_dict)
    """

    def parse(self, markdown: str) -> dict[str, Any]:
        """
        Parse markdown content into DesignSpecification dict.

        Args:
            markdown: Markdown-formatted design specification

        Returns:
            Dictionary with DesignSpecification fields

        Raises:
            ValueError: If required sections missing or malformed
        """
        # Extract major sections
        sections = self._extract_sections(markdown)

        # Parse metadata
        task_id = self._extract_task_id(markdown)
        timestamp = self._extract_timestamp(markdown)

        # Parse each section
        result = {
            "task_id": task_id,
            "architecture_overview": self._parse_architecture_overview(sections.get("Architecture Overview", "")),
            "technology_stack": self._parse_technology_stack(sections.get("Technology Stack", "")),
            "assumptions": self._parse_assumptions(sections.get("Assumptions", "")),
            "api_contracts": self._parse_api_contracts(sections.get("API Contracts", "")),
            "data_schemas": self._parse_data_schemas(sections.get("Data Schemas", "")),
            "component_logic": self._parse_component_logic(sections.get("Component Logic", "")),
            "design_review_checklist": self._parse_design_review_checklist(sections.get("Design Review Checklist", "")),
        }

        # Add timestamp if found
        if timestamp:
            result["timestamp"] = timestamp

        return result

    def _extract_sections(self, markdown: str) -> dict[str, str]:
        """
        Extract major sections from markdown.

        Sections are identified by ## headers.

        Returns:
            Dictionary mapping section names to content
        """
        sections = {}

        # Pattern: ## Section Name followed by content until next ## or end
        pattern = r'^## (.+?)$\n(.*?)(?=^## |\Z)'
        matches = re.finditer(pattern, markdown, re.MULTILINE | re.DOTALL)

        for match in matches:
            section_name = match.group(1).strip()
            section_content = match.group(2).strip()
            sections[section_name] = section_content

        return sections

    def _extract_task_id(self, markdown: str) -> str:
        """Extract task ID from title and metadata."""
        # Try title: # Design Specification: TASK-ID
        title_match = re.search(r'^# Design Specification: (.+?)$', markdown, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()

        # Try metadata: **Task ID:** TASK-ID
        metadata_match = re.search(r'\*\*Task ID:\*\* (.+?)$', markdown, re.MULTILINE)
        if metadata_match:
            return metadata_match.group(1).strip()

        raise ValueError("Task ID not found in markdown (expected in title or metadata)")

    def _extract_timestamp(self, markdown: str) -> Optional[datetime]:
        """Extract timestamp from metadata."""
        match = re.search(r'\*\*Timestamp:\*\* (.+?)$', markdown, re.MULTILINE)
        if match:
            timestamp_str = match.group(1).strip()
            try:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                # If parsing fails, return None (will use default in Pydantic)
                return None
        return None

    def _parse_architecture_overview(self, content: str) -> str:
        """Parse architecture overview section."""
        # Architecture is plain text paragraph
        if not content or len(content.strip()) < 50:
            raise ValueError("Architecture overview must be at least 50 characters")
        return content.strip()

    def _parse_technology_stack(self, content: str) -> dict[str, str]:
        """
        Parse technology stack section.

        Expected format:
        - **Language:** Python 3.12
        - **Framework:** FastAPI 0.104.1
        """
        tech_stack = {}

        # Pattern: - **Key:** Value
        pattern = r'- \*\*(.+?):\*\* (.+?)$'
        matches = re.finditer(pattern, content, re.MULTILINE)

        for match in matches:
            key = match.group(1).strip().lower().replace(' ', '_')
            value = match.group(2).strip()
            tech_stack[key] = value

        if not tech_stack:
            raise ValueError("Technology stack must have at least one technology specified")

        return tech_stack

    def _parse_assumptions(self, content: str) -> list[str]:
        """
        Parse assumptions section.

        Expected format:
        - Assumption 1
        - Assumption 2
        """
        assumptions = []

        # Pattern: - Assumption text
        pattern = r'^- (.+?)$'
        matches = re.finditer(pattern, content, re.MULTILINE)

        for match in matches:
            assumption = match.group(1).strip()
            assumptions.append(assumption)

        return assumptions

    def _parse_api_contracts(self, content: str) -> list[dict[str, Any]]:
        """
        Parse API contracts section.

        Expected format:
        ### GET /endpoint
        **Description:** ...
        **Authentication Required:** Yes/No
        ...
        """
        contracts = []

        # Split by ### headers (each API endpoint)
        endpoint_sections = re.split(r'^### (.+?)$', content, flags=re.MULTILINE)[1:]

        # Process pairs: (header, content)
        for i in range(0, len(endpoint_sections), 2):
            if i + 1 >= len(endpoint_sections):
                break

            header = endpoint_sections[i].strip()
            endpoint_content = endpoint_sections[i + 1].strip()

            # Parse method and endpoint from header (e.g., "GET /hello")
            method_endpoint_match = re.match(r'(GET|POST|PUT|DELETE|PATCH)\s+(.+)', header)
            if not method_endpoint_match:
                continue

            method = method_endpoint_match.group(1)
            endpoint = method_endpoint_match.group(2)

            # Parse fields
            description = self._extract_field(endpoint_content, "Description")
            auth_required = self._extract_field(endpoint_content, "Authentication Required")
            rate_limit = self._extract_field(endpoint_content, "Rate Limit")

            # Parse request params
            request_params = self._parse_request_params(endpoint_content)

            # Parse request body
            request_schema = self._parse_json_block(endpoint_content, "Request Body:")

            # Parse response schema
            response_schema = self._parse_json_block(endpoint_content, "Response \\(Success\\):")

            # Parse error responses
            error_responses = self._parse_error_responses(endpoint_content)

            contract = {
                "endpoint": endpoint,
                "method": method,
                "description": description,
                "request_params": request_params,
                "request_schema": request_schema,
                "response_schema": response_schema or {},
                "error_responses": error_responses,
                "authentication_required": auth_required.lower() in ("yes", "true") if auth_required else False,
                "rate_limit": rate_limit if rate_limit and rate_limit.lower() != "n/a" else None,
            }

            contracts.append(contract)

        return contracts

    def _parse_data_schemas(self, content: str) -> list[dict[str, Any]]:
        """
        Parse data schemas section.

        Expected format:
        ### Table: table_name
        **Description:** ...
        **Columns:**
        | Column | Type | Constraints |
        ...
        """
        schemas = []

        if not content or content.strip() == "":
            return schemas

        # Split by ### headers (each table)
        table_sections = re.split(r'^### Table: (.+?)$', content, flags=re.MULTILINE)[1:]

        # Process pairs: (table_name, content)
        for i in range(0, len(table_sections), 2):
            if i + 1 >= len(table_sections):
                break

            table_name = table_sections[i].strip()
            table_content = table_sections[i + 1].strip()

            # Parse description
            description = self._extract_field(table_content, "Description")

            # Parse columns from markdown table
            columns = self._parse_table_columns(table_content)

            # Parse indexes (SQL code blocks)
            indexes = self._parse_sql_statements(table_content, "Indexes:")

            # Parse relationships (SQL code blocks)
            relationships = self._parse_sql_statements(table_content, "Relationships:")

            # Parse constraints (SQL code blocks)
            constraints = self._parse_sql_statements(table_content, "Constraints:")

            schema = {
                "table_name": table_name,
                "description": description,
                "columns": columns,
                "indexes": indexes,
                "relationships": relationships,
                "constraints": constraints,
            }

            schemas.append(schema)

        return schemas

    def _parse_component_logic(self, content: str) -> list[dict[str, Any]]:
        """
        Parse component logic section.

        Expected format:
        ### Component: ComponentName
        **Semantic Unit:** SU-XXX
        **Responsibility:** ...
        ...
        """
        components = []

        # Split by ### Component: headers
        component_sections = re.split(r'^### Component: (.+?)$', content, flags=re.MULTILINE)[1:]

        # Process pairs: (component_name, content)
        for i in range(0, len(component_sections), 2):
            if i + 1 >= len(component_sections):
                break

            component_name = component_sections[i].strip()
            component_content = component_sections[i + 1].strip()

            # Parse fields
            semantic_unit_id = self._extract_field(component_content, "Semantic Unit")
            responsibility = self._extract_field(component_content, "Responsibility")
            implementation_notes = self._extract_implementation_notes(component_content)
            complexity = self._extract_complexity(component_content)

            # Parse dependencies
            dependencies = self._parse_dependencies(component_content)

            # Parse interfaces (method signatures)
            interfaces = self._parse_interfaces(component_content)

            component = {
                "component_name": component_name,
                "semantic_unit_id": semantic_unit_id,
                "responsibility": responsibility,
                "interfaces": interfaces,
                "dependencies": dependencies,
                "implementation_notes": implementation_notes,
            }

            if complexity is not None:
                component["complexity"] = complexity

            components.append(component)

        return components

    def _parse_design_review_checklist(self, content: str) -> list[dict[str, Any]]:
        """
        Parse design review checklist section.

        Expected format:
        ### Category: Description
        **Validation Criteria:** ...
        **Severity:** Critical/High/Medium/Low
        """
        checklist = []

        # Split by ### headers (each checklist item)
        item_sections = re.split(r'^### (.+?)$', content, flags=re.MULTILINE)[1:]

        # Process pairs: (header, content)
        for i in range(0, len(item_sections), 2):
            if i + 1 >= len(item_sections):
                break

            header = item_sections[i].strip()
            item_content = item_sections[i + 1].strip()

            # Parse category and description from header (e.g., "Security: Password handling")
            category_desc_match = re.match(r'(.+?):\s*(.+)', header)
            if category_desc_match:
                category = category_desc_match.group(1).strip()
                description = category_desc_match.group(2).strip()
            else:
                # Fallback: use whole header as description, generic category
                category = "General"
                description = header

            # Parse fields
            validation_criteria = self._extract_field(item_content, "Validation Criteria")
            severity = self._extract_field(item_content, "Severity")

            item = {
                "category": category,
                "description": description,
                "validation_criteria": validation_criteria,
                "severity": severity or "Medium",
            }

            checklist.append(item)

        return checklist

    # Helper methods

    def _extract_field(self, content: str, field_name: str) -> str:
        """Extract field value after bold label."""
        pattern = rf'\*\*{re.escape(field_name)}:\*\*\s*(.+?)(?:\n|$)'
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(1).strip() if match else ""

    def _parse_json_block(self, content: str, header: str) -> Optional[dict[str, Any]]:
        """Parse JSON from code block after header."""
        # Pattern: header followed by ```json ... ```
        pattern = rf'{re.escape(header)}\s*```json\s*\n(.+?)\n```'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            json_str = match.group(1).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Try to fix common issues
                json_str = json_str.replace("'", '"')
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    return None

        return None

    def _parse_request_params(self, content: str) -> Optional[dict[str, str]]:
        """
        Parse request parameters section.

        Expected format:
        **Request Parameters:**
        - `param_name`: type and description
        """
        # Find Request Parameters section
        pattern = r'\*\*Request Parameters:\*\*\s*\n((?:- `.+`:.+\n?)+)'
        match = re.search(pattern, content, re.MULTILINE)

        if not match:
            return None

        params_content = match.group(1)
        params = {}

        # Parse each parameter line
        param_pattern = r'- `(.+?)`: (.+?)(?:\n|$)'
        param_matches = re.finditer(param_pattern, params_content)

        for param_match in param_matches:
            param_name = param_match.group(1).strip()
            param_desc = param_match.group(2).strip()
            params[param_name] = param_desc

        return params if params else None

    def _parse_error_responses(self, content: str) -> list[dict[str, Any]]:
        """
        Parse error responses section.

        Expected format:
        **Error Responses:**
        - **400 ERROR_CODE**: Message
        """
        errors = []

        # Find Error Responses section
        pattern = r'\*\*Error Responses:\*\*\s*\n((?:- \*\*.+\*\*:.+\n?)+)'
        match = re.search(pattern, content, re.MULTILINE)

        if not match:
            return errors

        errors_content = match.group(1)

        # Parse each error line: - **STATUS CODE**: Message
        error_pattern = r'- \*\*(\d+)\s+([A-Z_]+)\*\*:\s*(.+?)(?:\n|$)'
        error_matches = re.finditer(error_pattern, errors_content)

        for error_match in error_matches:
            status = int(error_match.group(1))
            code = error_match.group(2).strip()
            message = error_match.group(3).strip()

            errors.append({
                "status": status,
                "code": code,
                "message": message,
            })

        return errors

    def _parse_table_columns(self, content: str) -> list[dict[str, Any]]:
        """
        Parse columns from markdown table.

        Expected format:
        | Column | Type | Constraints |
        |--------|------|-------------|
        | col1   | TYPE | constraints |
        """
        columns = []

        # Find table after **Columns:**
        pattern = r'\*\*Columns:\*\*\s*\n\|.+\|.+\n\|[-\s|]+\n((?:\|.+\|\n?)+)'
        match = re.search(pattern, content, re.MULTILINE)

        if not match:
            return columns

        table_rows = match.group(1).strip().split('\n')

        for row in table_rows:
            # Parse: | column | type | constraints |
            cells = [cell.strip() for cell in row.split('|')[1:-1]]
            if len(cells) >= 3:
                columns.append({
                    "name": cells[0],
                    "type": cells[1],
                    "constraints": cells[2],
                })

        return columns

    def _parse_sql_statements(self, content: str, header: str) -> list[str]:
        """
        Parse SQL statements from code block after header.

        Expected format:
        **Header:**
        ```sql
        STATEMENT1;
        STATEMENT2;
        ```
        """
        statements = []

        # Pattern: header followed by ```sql ... ```
        pattern = rf'\*\*{re.escape(header)}\*\*\s*```sql\s*\n(.+?)\n```'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            sql_block = match.group(1).strip()
            # Split by semicolons, clean up
            for stmt in sql_block.split(';'):
                stmt = stmt.strip()
                if stmt:
                    statements.append(stmt + ';')

        return statements

    def _parse_dependencies(self, content: str) -> list[str]:
        """
        Parse dependencies section.

        Expected format:
        **Dependencies:**
        - Component1
        - Component2
        """
        dependencies = []

        # Find Dependencies section
        pattern = r'\*\*Dependencies:\*\*\s*\n((?:- .+\n?)+)'
        match = re.search(pattern, content, re.MULTILINE)

        if not match:
            return dependencies

        deps_content = match.group(1)

        # Parse each dependency line
        dep_pattern = r'^- (.+?)$'
        dep_matches = re.finditer(dep_pattern, deps_content, re.MULTILINE)

        for dep_match in dep_matches:
            dep = dep_match.group(1).strip()
            if dep.lower() != "none":
                dependencies.append(dep)

        return dependencies

    def _parse_interfaces(self, content: str) -> list[dict[str, Any]]:
        """
        Parse interface methods section.

        Expected format:
        #### `method_name(param: type) -> return_type`
        Description
        **Parameters:**
        - `param`: description
        **Returns:** description
        """
        interfaces = []

        # Find Interfaces section
        interfaces_pattern = r'\*\*Interfaces:\*\*\s*\n(.+?)(?=\*\*Implementation Notes:|\Z)'
        interfaces_match = re.search(interfaces_pattern, content, re.DOTALL)

        if not interfaces_match:
            return interfaces

        interfaces_content = interfaces_match.group(1)

        # Split by #### headers (each method)
        method_sections = re.split(r'^#### `(.+?)`$', interfaces_content, flags=re.MULTILINE)[1:]

        # Process pairs: (signature, content)
        for i in range(0, len(method_sections), 2):
            if i + 1 >= len(method_sections):
                break

            signature = method_sections[i].strip()
            method_content = method_sections[i + 1].strip()

            # Parse signature: method_name(params) -> return_type
            sig_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\((.*?)\)\s*->\s*(.+)', signature)

            if sig_match:
                method_name = sig_match.group(1)
                params_str = sig_match.group(2)
                returns = sig_match.group(3).strip()

                # Parse parameters
                parameters = {}
                if params_str:
                    # Split by comma (simple approach)
                    for param in params_str.split(','):
                        param = param.strip()
                        if ':' in param:
                            param_name, param_type = param.split(':', 1)
                            parameters[param_name.strip()] = param_type.strip()

                # Extract description (first paragraph)
                description_match = re.search(r'^(.+?)(?:\n\n|\*\*|$)', method_content, re.DOTALL)
                description = description_match.group(1).strip() if description_match else ""

                interface = {
                    "method": method_name,
                    "parameters": parameters,
                    "returns": returns,
                    "description": description,
                }

                interfaces.append(interface)

        return interfaces

    def _extract_implementation_notes(self, content: str) -> str:
        """Extract implementation notes section."""
        pattern = r'\*\*Implementation Notes:\*\*\s*\n(.+?)(?=\*\*Estimated Complexity:|\Z)'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            notes = match.group(1).strip()
            # Remove any trailing separators
            notes = re.sub(r'\n---\s*$', '', notes)
            return notes

        return ""

    def _extract_complexity(self, content: str) -> Optional[int]:
        """Extract estimated complexity value."""
        pattern = r'\*\*Estimated Complexity:\*\*\s*(\d+)'
        match = re.search(pattern, content)

        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None

        return None
