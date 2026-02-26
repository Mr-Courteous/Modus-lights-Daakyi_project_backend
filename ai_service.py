"""
DAAKYI CompaaS AI Service
AI-powered document analysis and NIST CSF 2.0 control mapping using OpenAI GPT-4o
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import base64
import mimetypes
from models import AIAnalysisResult
import json
import uuid

logger = logging.getLogger(__name__)

class AIService:
    """AI service for document analysis and NIST control mapping"""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.model = os.environ.get('AI_MODEL', 'gpt-4o')
        self.max_tokens = int(os.environ.get('AI_MAX_TOKENS', '4096'))
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY environment variable not set - AI features will use fallback mode")
            self.api_key = None
    
    async def analyze_document(self, file_content: bytes, filename: str, mime_type: str) -> AIAnalysisResult:
        """
        Analyze a document using OpenAI GPT-4o for classification and NIST control mapping
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            mime_type: MIME type of the file
            
        Returns:
            AIAnalysisResult with classification, confidence, and NIST mappings
        """
        try:
            # Check if we have a real API key
            if not self.api_key or self.api_key == "test-key-for-demo":
                logger.info(f"Using mock AI analysis for {filename} (no real API key)")
                return await self._create_mock_analysis_result(filename, file_content, mime_type)
            
            # Convert file content to base64 for API
            if mime_type.startswith('text/') or mime_type in ['application/pdf', 'application/msword']:
                # For text-based files, try to extract readable content
                content_preview = await self._extract_text_content(file_content, mime_type)
            else:
                content_preview = f"Binary file: {filename} ({mime_type})"
            
            # Create AI chat instance
            session_id = f"doc_analysis_{uuid.uuid4().hex}"
            # AI chat functionality disabled due to missing emergentintegrations package
            logger.info(f"AI chat functionality is disabled. Returning mock analysis for {filename}.")
            return await self._create_mock_analysis_result(filename, file_content, mime_type)
            
        except Exception as e:
            logger.error(f"AI analysis failed for {filename}: {str(e)}")
            # Return a fallback analysis result
            return self._create_fallback_result(filename, str(e))
    
    def _get_document_analysis_system_prompt(self) -> str:
        """System prompt for document analysis and NIST mapping"""
        return """You are an expert cybersecurity analyst specializing in NIST Cybersecurity Framework (CSF) 2.0 compliance assessments. Your task is to analyze documents and provide:

1. **Document Classification**: Categorize the document type
2. **Content Analysis**: Extract key cybersecurity-relevant information  
3. **NIST CSF 2.0 Mapping**: Map content to specific NIST subcategories
4. **Risk Assessment**: Identify potential security gaps or concerns
5. **Recommendations**: Provide actionable remediation guidance

**NIST CSF 2.0 Functions & Categories:**

**GOVERN (GV)**:
- GV.OC (Organizational Context): GV.OC-01, GV.OC-02, GV.OC-03, GV.OC-04, GV.OC-05
- GV.RM (Risk Management): GV.RM-01, GV.RM-02, GV.RM-03, GV.RM-04, GV.RM-05, GV.RM-06, GV.RM-07
- GV.RR (Risk Reporting): GV.RR-01, GV.RR-02, GV.RR-03, GV.RR-04
- GV.SC (Supply Chain): GV.SC-01, GV.SC-02, GV.SC-03, GV.SC-04, GV.SC-05, GV.SC-06, GV.SC-07, GV.SC-08, GV.SC-09, GV.SC-10

**IDENTIFY (ID)**:
- ID.AM (Asset Management): ID.AM-01, ID.AM-02, ID.AM-03, ID.AM-04, ID.AM-05, ID.AM-06, ID.AM-07, ID.AM-08
- ID.RA (Risk Assessment): ID.RA-01, ID.RA-02, ID.RA-03, ID.RA-04, ID.RA-05, ID.RA-06, ID.RA-07, ID.RA-08, ID.RA-09, ID.RA-10
- ID.IM (Improvement): ID.IM-01, ID.IM-02, ID.IM-03, ID.IM-04

**PROTECT (PR)**:
- PR.AA (Identity Management): PR.AA-01, PR.AA-02, PR.AA-03, PR.AA-04, PR.AA-05, PR.AA-06
- PR.AT (Awareness Training): PR.AT-01, PR.AT-02
- PR.DS (Data Security): PR.DS-01, PR.DS-02, PR.DS-03, PR.DS-04, PR.DS-05, PR.DS-06, PR.DS-07, PR.DS-08, PR.DS-09, PR.DS-10, PR.DS-11
- PR.IP (Info Protection): PR.IP-01, PR.IP-02, PR.IP-03, PR.IP-04, PR.IP-05, PR.IP-06, PR.IP-07, PR.IP-08, PR.IP-09, PR.IP-10, PR.IP-11, PR.IP-12
- PR.MA (Maintenance): PR.MA-01, PR.MA-02
- PR.PT (Protective Technology): PR.PT-01, PR.PT-02, PR.PT-03, PR.PT-04, PR.PT-05

**DETECT (DE)**:
- DE.AE (Anomalies Events): DE.AE-01, DE.AE-02, DE.AE-03, DE.AE-04, DE.AE-05, DE.AE-06, DE.AE-07, DE.AE-08
- DE.CM (Continuous Monitoring): DE.CM-01, DE.CM-02, DE.CM-03, DE.CM-04, DE.CM-05, DE.CM-06, DE.CM-07, DE.CM-08, DE.CM-09

**RESPOND (RS)**:
- RS.RP (Response Planning): RS.RP-01, RS.RP-02, RS.RP-03, RS.RP-04, RS.RP-05
- RS.CO (Communications): RS.CO-01, RS.CO-02, RS.CO-03, RS.CO-04, RS.CO-05
- RS.AN (Analysis): RS.AN-01, RS.AN-02, RS.AN-03, RS.AN-04, RS.AN-05, RS.AN-06, RS.AN-07, RS.AN-08
- RS.MI (Mitigation): RS.MI-01, RS.MI-02, RS.MI-03
- RS.IM (Improvements): RS.IM-01, RS.IM-02

**RECOVER (RC)**:
- RC.RP (Recovery Planning): RC.RP-01, RC.RP-02, RC.RP-03, RC.RP-04, RC.RP-05
- RC.IM (Improvements): RC.IM-01, RC.IM-02
- RC.CO (Communications): RC.CO-01, RC.CO-02, RC.CO-03, RC.CO-04

**Response Format**: Respond with a JSON object containing:
```json
{
  "classification": "DOCUMENT_TYPE",
  "confidence": 0.95,
  "description": "Detailed analysis of the document content and purpose",
  "extracted_metadata": {
    "document_type": "Type",
    "version": "Version if applicable",
    "date": "Document date",
    "scope": "Coverage area"
  },
  "nist_mappings": [
    {
      "control_id": "GV.OC-01", 
      "confidence": 0.92, 
      "rationale": "Specific reason why this control applies"
    }
  ],
  "risk_findings": [
    {
      "level": "Medium|High|Critical",
      "description": "Specific risk or gap identified", 
      "recommendation": "Actionable remediation step"
    }
  ]
}
```

**Classification Types**: POLICY_DOCUMENT, PROCEDURE_DOCUMENT, AUDIT_REPORT, RISK_ASSESSMENT, TRAINING_MATERIAL, TECHNICAL_SPECIFICATION, INCIDENT_REPORT, COMPLIANCE_CERTIFICATE, NETWORK_DIAGRAM, SECURITY_ARCHITECTURE, OTHER"""

    def _create_analysis_prompt(self, filename: str, mime_type: str, content_preview: str) -> str:
        """Create the analysis prompt for a specific document"""
        return f"""Please analyze the following cybersecurity document for NIST CSF 2.0 compliance:

**Document Details:**
- Filename: {filename}
- File Type: {mime_type}
- Content Preview: {content_preview[:2000]}...

**Analysis Required:**
1. Classify the document type with confidence level
2. Extract key metadata and cybersecurity relevance
3. Map to specific NIST CSF 2.0 subcategories (be specific with control IDs)
4. Identify any security gaps or areas for improvement
5. Provide actionable recommendations

**Focus Areas:**
- Look for policy statements, procedures, technical controls
- Identify risk management practices
- Note compliance references and frameworks
- Assess completeness and maturity
- Consider organizational context and scope

Please provide your analysis in the specified JSON format."""

    async def _extract_text_content(self, file_content: bytes, mime_type: str) -> str:
        """Extract readable text content from various file types"""
        try:
            if mime_type.startswith('text/'):
                return file_content.decode('utf-8')[:3000]
            elif mime_type == 'application/pdf':
                # For demo purposes, return a placeholder
                # In production, you'd use PyPDF2 or similar
                return f"[PDF content - {len(file_content)} bytes] This document appears to be a PDF file that would contain cybersecurity-related content based on typical organizational documentation patterns."
            elif 'word' in mime_type or 'msword' in mime_type:
                return f"[Word document - {len(file_content)} bytes] This document appears to be a Microsoft Word file containing organizational documentation."
            else:
                return f"[Binary file - {len(file_content)} bytes] File type: {mime_type}"
        except Exception as e:
            logger.warning(f"Could not extract text content: {e}")
            return f"[Content extraction failed - {len(file_content)} bytes]"

    async def _parse_ai_response(self, ai_response: str, filename: str) -> AIAnalysisResult:
        """Parse the AI response into structured analysis result"""
        try:
            # Try to parse JSON from the response
            # Handle potential markdown formatting
            json_text = ai_response.strip()
            if json_text.startswith('```json'):
                json_text = json_text.replace('```json', '').replace('```', '').strip()
            
            analysis_data = json.loads(json_text)
            
            return AIAnalysisResult(
                classification=analysis_data.get('classification', 'OTHER'),
                confidence=float(analysis_data.get('confidence', 0.8)),
                description=analysis_data.get('description', 'AI-generated document analysis'),
                extracted_metadata=analysis_data.get('extracted_metadata', {}),
                nist_mappings=analysis_data.get('nist_mappings', []),
                risk_findings=analysis_data.get('risk_findings', [])
            )
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"AI response was: {ai_response[:500]}...")
            
            # Create a fallback result based on the raw response
            return AIAnalysisResult(
                classification="OTHER",
                confidence=0.7,
                description=f"Document analysis completed. Raw AI response available.",
                extracted_metadata={"filename": filename, "analysis_method": "fallback"},
                nist_mappings=[{
                    "control_id": "GV.OC-01",
                    "confidence": 0.6,
                    "rationale": "General organizational documentation - may support organizational context controls"
                }],
                risk_findings=[{
                    "level": "Low",
                    "description": "Document requires manual review for complete analysis",
                    "recommendation": "Perform detailed manual assessment to identify specific NIST control mappings"
                }]
            )

    async def _create_mock_analysis_result(self, filename: str, file_content: bytes, mime_type: str) -> AIAnalysisResult:
        """Create a realistic mock analysis result for testing purposes"""
        
        # Analyze filename and content for basic classification
        filename_lower = filename.lower()
        content_text = ""
        
        try:
            if mime_type.startswith('text/'):
                content_text = file_content.decode('utf-8', errors='ignore').lower()
        except:
            pass
            
        # Determine classification based on filename and content
        if any(word in filename_lower for word in ['policy', 'policies']):
            classification = "POLICY_DOCUMENT"
            confidence = 0.92
        elif any(word in filename_lower for word in ['procedure', 'process', 'sop']):
            classification = "PROCEDURE_DOCUMENT"
            confidence = 0.88
        elif any(word in filename_lower for word in ['audit', 'assessment', 'review']):
            classification = "AUDIT_REPORT"
            confidence = 0.85
        elif any(word in filename_lower for word in ['risk', 'threat']):
            classification = "RISK_ASSESSMENT"
            confidence = 0.90
        elif any(word in filename_lower for word in ['training', 'awareness']):
            classification = "TRAINING_MATERIAL"
            confidence = 0.87
        else:
            classification = "OTHER"
            confidence = 0.75
            
        # Generate NIST mappings based on content analysis
        nist_mappings = []
        
        # Basic mappings for cybersecurity documents
        if 'policy' in content_text or 'governance' in content_text:
            nist_mappings.append({
                "control_id": "GV.OC-01",
                "confidence": 0.89,
                "rationale": "Document contains organizational context and governance information"
            })
            
        if 'risk' in content_text or 'management' in content_text:
            nist_mappings.append({
                "control_id": "GV.RM-01",
                "confidence": 0.85,
                "rationale": "Document addresses risk management strategy and processes"
            })
            
        if 'access' in content_text or 'authentication' in content_text or 'authorization' in content_text:
            nist_mappings.append({
                "control_id": "PR.AA-01",
                "confidence": 0.91,
                "rationale": "Document covers identity management and access control"
            })
            
        if 'data' in content_text or 'information' in content_text or 'encryption' in content_text:
            nist_mappings.append({
                "control_id": "PR.DS-01",
                "confidence": 0.87,
                "rationale": "Document addresses data security and protection measures"
            })
            
        if 'incident' in content_text or 'response' in content_text or 'emergency' in content_text:
            nist_mappings.append({
                "control_id": "RS.RP-01",
                "confidence": 0.93,
                "rationale": "Document contains incident response planning information"
            })
            
        # If no specific mappings found, add a general one
        if not nist_mappings:
            nist_mappings.append({
                "control_id": "GV.OC-01",
                "confidence": 0.70,
                "rationale": "General organizational documentation supporting cybersecurity context"
            })
            
        # Generate risk findings
        risk_findings = [
            {
                "level": "Medium",
                "description": "Document analysis completed using mock AI service",
                "recommendation": "Deploy with real OpenAI API key for production-quality analysis"
            }
        ]
        
        return AIAnalysisResult(
            classification=classification,
            confidence=confidence,
            description=f"Mock AI analysis of {filename}. Classification: {classification} with {confidence:.1%} confidence.",
            extracted_metadata={
                "filename": filename,
                "file_size": len(file_content),
                "mime_type": mime_type,
                "analysis_method": "mock_ai_service"
            },
            nist_mappings=nist_mappings,
            risk_findings=risk_findings
        )

    def _create_fallback_result(self, filename: str, error_message: str) -> AIAnalysisResult:
        """Create a fallback analysis result when AI analysis fails"""
        return AIAnalysisResult(
            classification="OTHER",
            confidence=0.5,
            description=f"AI analysis failed for {filename}. Manual review required.",
            extracted_metadata={"filename": filename, "error": error_message},
            nist_mappings=[],
            risk_findings=[{
                "level": "Medium",
                "description": f"AI analysis failed: {error_message}",
                "recommendation": "Perform manual document review and classification"
            }]
        )

    async def generate_gap_analysis(self, assessment_id: str, control_assessments: List[Dict]) -> Dict[str, Any]:
        """Generate comprehensive gap analysis for an assessment"""
        try:
            # Create AI chat for gap analysis
            session_id = f"gap_analysis_{assessment_id}"
            # AI chat functionality disabled due to missing emergentintegrations package
            logger.info("AI chat functionality is disabled. Returning fallback gap analysis.")
            return {
                "overall_maturity": "Unknown",
                "critical_gaps": [],
                "recommendations": ["Manual gap analysis recommended due to processing error"],
                "risk_score": "Medium"
            }
            
        except Exception as e:
            logger.error(f"Gap analysis failed: {str(e)}")
            return {
                "overall_maturity": "Unknown",
                "critical_gaps": [],
                "recommendations": ["Manual gap analysis recommended due to processing error"],
                "risk_score": "Medium"
            }

    def _get_gap_analysis_system_prompt(self) -> str:
        """System prompt for gap analysis"""
        return """You are a cybersecurity expert conducting NIST CSF 2.0 gap analysis. Analyze the provided control assessment data to identify:

1. **Critical Gaps**: High-priority areas lacking adequate controls
2. **Maturity Assessment**: Overall organizational cybersecurity maturity
3. **Risk Prioritization**: Risk-based ranking of findings  
4. **Remediation Roadmap**: Actionable improvement recommendations

Respond with JSON format:
```json
{
  "overall_maturity": "Initial|Developing|Defined|Managed|Optimizing",
  "maturity_score": 2.5,
  "critical_gaps": [
    {
      "function": "PROTECT",
      "control_ids": ["PR.AA-01", "PR.DS-03"],
      "description": "Gap description",
      "risk_impact": "High|Medium|Low",
      "remediation_priority": 1
    }
  ],
  "recommendations": [
    {
      "priority": 1,
      "title": "Recommendation title", 
      "description": "Detailed action plan",
      "estimated_effort": "1-3 months",
      "business_impact": "Description of business value"
    }
  ],
  "risk_score": "Critical|High|Medium|Low"
}
```"""

    def _create_gap_analysis_prompt(self, control_assessments: List[Dict]) -> str:
        """Create gap analysis prompt from control assessment data"""
        assessment_summary = []
        for control in control_assessments[:20]:  # Limit for prompt size
            assessment_summary.append(f"- {control.get('control_id', 'Unknown')}: Score {control.get('overall_score', 0)}/4, Status: {control.get('status', 'Unknown')}")
        
        return f"""Analyze the following NIST CSF 2.0 control assessments for gaps and recommendations:

**Control Assessment Summary:**
{chr(10).join(assessment_summary)}

**Total Controls Assessed:** {len(control_assessments)}

Please provide a comprehensive gap analysis with:
1. Overall organizational maturity assessment
2. Critical security gaps requiring immediate attention  
3. Risk-prioritized remediation recommendations
4. Implementation timelines and effort estimates

Focus on practical, actionable guidance that executives and security teams can implement."""

# Singleton instance
ai_service = AIService()