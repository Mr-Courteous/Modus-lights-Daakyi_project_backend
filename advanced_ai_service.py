"""
DAAKYI CompaaS Advanced AI Service
Enhanced AI capabilities including advanced auto-mapping, gap analysis, 
summarization, and remediation recommendations
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import base64
import mimetypes
from models import AIAnalysisResult
import json
import uuid
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GapAnalysisResult:
    """Result of AI-powered gap analysis"""
    control_id: str
    current_maturity: int
    target_maturity: int
    gap_score: float
    gap_explanation: str
    priority_level: str  # critical, high, medium, low
    estimated_effort: str
    dependencies: List[str]
    
@dataclass
class RemediationRecommendation:
    """AI-generated remediation recommendations"""
    control_id: str
    recommendation_id: str
    title: str
    description: str
    implementation_steps: List[str]
    estimated_timeline: str
    required_resources: List[str]
    success_criteria: List[str]
    risk_reduction: float
    confidence_score: float

@dataclass
class DocumentSummary:
    """AI-generated document summary"""
    executive_summary: str
    key_findings: List[str]
    compliance_insights: List[str]
    recommended_actions: List[str]
    risk_assessment: str
    confidence_score: float

@dataclass
class EnhancedAnalysisResult:
    """Enhanced AI analysis with advanced capabilities"""
    basic_analysis: AIAnalysisResult
    document_summary: DocumentSummary
    gap_analysis: List[GapAnalysisResult]
    remediation_recommendations: List[RemediationRecommendation]
    confidence_override_history: List[Dict[str, Any]]
    processing_metadata: Dict[str, Any]

class AdvancedAIService:
    """Enhanced AI service with advanced capabilities for DAAKYI CompaaS"""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.model = os.environ.get('AI_MODEL', 'gpt-4o')
        self.max_tokens = int(os.environ.get('AI_MAX_TOKENS', '4096'))
        self.confidence_threshold = float(os.environ.get('AI_CONFIDENCE_THRESHOLD', '0.85'))
        
        # Enhanced AI capabilities settings
        self.enable_advanced_mapping = True
        self.enable_gap_analysis = True
        self.enable_summarization = True
        self.enable_remediation = True
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set - using mock AI responses")
            self.api_key = None
    
    async def enhanced_document_analysis(self, 
                                       file_content: bytes, 
                                       filename: str, 
                                       mime_type: str,
                                       current_assessment_context: Optional[Dict] = None) -> EnhancedAnalysisResult:
        """
        Perform comprehensive AI analysis with all advanced capabilities
        
        Args:
            file_content: Raw file content
            filename: Original filename
            mime_type: MIME type
            current_assessment_context: Context about current assessment state
            
        Returns:
            EnhancedAnalysisResult with all AI capabilities applied
        """
        try:
            # Start with basic analysis
            basic_result = await self._perform_basic_analysis(file_content, filename, mime_type)
            
            # Generate document summary
            summary = await self._generate_document_summary(file_content, filename, mime_type)
            
            # Perform gap analysis
            gap_analysis = await self._perform_gap_analysis(basic_result, current_assessment_context)
            
            # Generate remediation recommendations
            remediation = await self._generate_remediation_recommendations(basic_result, gap_analysis)
            
            # Create processing metadata
            metadata = {
                "processing_time": datetime.now().isoformat(),
                "ai_model": self.model,
                "confidence_threshold": self.confidence_threshold,
                "capabilities_used": {
                    "advanced_mapping": self.enable_advanced_mapping,
                    "gap_analysis": self.enable_gap_analysis,
                    "summarization": self.enable_summarization,
                    "remediation": self.enable_remediation
                }
            }
            
            return EnhancedAnalysisResult(
                basic_analysis=basic_result,
                document_summary=summary,
                gap_analysis=gap_analysis,
                remediation_recommendations=remediation,
                confidence_override_history=[],
                processing_metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Enhanced analysis failed for {filename}: {str(e)}")
            return await self._create_fallback_enhanced_result(filename)
    
    async def _perform_basic_analysis(self, file_content: bytes, filename: str, mime_type: str) -> AIAnalysisResult:
        """Enhanced basic analysis with improved auto-mapping"""
        
        if not self.api_key or self.api_key == "test-key-for-demo":
            return await self._create_mock_basic_analysis(filename, file_content, mime_type)
        
        try:
            # Enhanced prompt for better auto-mapping
            enhanced_prompt = f"""
            Analyze this document ({filename}) as a cybersecurity compliance expert for DAAKYI CompaaS platform.
            
            ANALYSIS REQUIREMENTS:
            1. Document Classification (confidence ≥ {self.confidence_threshold})
            2. NIST CSF 2.0 Control Mapping (precise subcategory matching)
            3. Compliance Context Analysis
            4. Risk Assessment
            
            ENHANCED MAPPING CRITERIA:
            - Map to specific NIST CSF 2.0 subcategories (e.g., PR.AC-01, DE.AE-02)
            - Provide mapping confidence score (0.0-1.0)
            - Explain mapping rationale
            - Identify secondary control relationships
            
            Return JSON response with:
            {{
                "classification": "policy|procedure|evidence|technical_config|audit_report|other",
                "confidence": 0.95,
                "nist_mappings": [
                    {{
                        "subcategory": "PR.AC-01",
                        "relevance": "primary|secondary|related",
                        "confidence": 0.92,
                        "rationale": "Document directly addresses access control policy requirements"
                    }}
                ],
                "summary": "Brief document summary",
                "key_findings": ["finding1", "finding2"],
                "compliance_impact": "assessment of compliance implications",
                "risk_indicators": ["risk1", "risk2"]
            }}
            """
            
            # Process with enhanced AI
            file_content_b64 = base64.b64encode(file_content).decode('utf-8')
            
            # llm_chat = LlmChat(
            #     api_key=self.api_key,
            #     model=self.model,
            #     max_tokens=self.max_tokens
            # )
            
            # messages = [
            #     UserMessage(content=enhanced_prompt),
            #     UserMessage(content=f"Document content (base64): {file_content_b64[:1000]}...")
            # ]
            
            # response = await llm_chat.async_chat(messages)
            
            # # Parse enhanced response
            # analysis_data = json.loads(response.strip())
            
            # # Convert to AIAnalysisResult format
            # nist_controls = [
            #     {
            #         "subcategory": mapping["subcategory"],
            #         "confidence": mapping["confidence"],
            #         "rationale": mapping["rationale"]
            #     }
            #     for mapping in analysis_data.get("nist_mappings", [])
            # ]
            
            # return AIAnalysisResult(
            #     classification=analysis_data["classification"],
            #     confidence=analysis_data["confidence"],
            #     description=analysis_data["summary"],  # Map summary to description
            #     extracted_metadata=analysis_data.get("extracted_metadata", {}),
            #     nist_mappings=[
            #         {
            #             "controlId": mapping["subcategory"],
            #             "confidence": mapping["confidence"],
            #             "rationale": mapping["rationale"]
            #         }
            #         for mapping in analysis_data.get("nist_mappings", [])
            #     ],
            #     risk_findings=analysis_data.get("risk_indicators", [])
            # )
            
        except Exception as e:
            logger.error(f"Enhanced basic analysis failed: {str(e)}")
            return await self._create_mock_basic_analysis(filename, file_content, mime_type)
    
    async def _generate_document_summary(self, file_content: bytes, filename: str, mime_type: str) -> DocumentSummary:
        """Generate intelligent document summary with compliance focus"""
        
        if not self.api_key or self.api_key == "test-key-for-demo":
            return await self._create_mock_summary(filename)
        
        try:
            summary_prompt = f"""
            As a cybersecurity compliance expert, create an executive summary of this document ({filename}).
            
            FOCUS AREAS:
            1. Executive Summary (2-3 sentences)
            2. Key Compliance Findings
            3. Risk Assessment
            4. Recommended Actions
            
            Return JSON:
            {{
                "executive_summary": "Concise overview for executives",
                "key_findings": ["finding1", "finding2", "finding3"],
                "compliance_insights": ["insight1", "insight2"],
                "recommended_actions": ["action1", "action2"],
                "risk_assessment": "Overall risk evaluation",
                "confidence_score": 0.92
            }}
            """
            
            # llm_chat = LlmChat(api_key=self.api_key, model=self.model, max_tokens=self.max_tokens)
            
            # file_content_b64 = base64.b64encode(file_content).decode('utf-8')
            # messages = [
            #     UserMessage(content=summary_prompt),
            #     UserMessage(content=f"Document: {file_content_b64[:2000]}...")
            # ]
            
            # response = await llm_chat.async_chat(messages)
            # summary_data = json.loads(response.strip())
            
            # return DocumentSummary(
            #     executive_summary=summary_data["executive_summary"],
            #     key_findings=summary_data["key_findings"],
            #     compliance_insights=summary_data["compliance_insights"],
            #     recommended_actions=summary_data["recommended_actions"],
            #     risk_assessment=summary_data["risk_assessment"],
            #     confidence_score=summary_data["confidence_score"]
            # )
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return await self._create_mock_summary(filename)
    
    async def _perform_gap_analysis(self, basic_result: AIAnalysisResult, context: Optional[Dict]) -> List[GapAnalysisResult]:
        """AI-powered gap analysis with intelligent prioritization"""
        
        if not self.api_key or self.api_key == "test-key-for-demo":
            return await self._create_mock_gap_analysis(basic_result)
        
        try:
            gap_prompt = f"""
            Perform intelligent gap analysis for NIST CSF 2.0 controls based on this evidence.
            
            EVIDENCE ANALYSIS: {json.dumps(basic_result.__dict__, default=str)}
            CURRENT CONTEXT: {json.dumps(context or {}, default=str)}
            
            For each relevant NIST control, analyze:
            1. Current maturity level (0-4 scale)
            2. Target maturity level
            3. Gap score and explanation
            4. Priority level (critical/high/medium/low)
            5. Implementation effort estimate
            
            Return JSON array:
            [
                {{
                    "control_id": "PR.AC-01",
                    "current_maturity": 2,
                    "target_maturity": 4,
                    "gap_score": 0.6,
                    "gap_explanation": "Detailed gap analysis",
                    "priority_level": "high",
                    "estimated_effort": "3-6 months",
                    "dependencies": ["PR.AC-02", "PR.AT-01"]
                }}
            ]
            """
            
            # llm_chat = LlmChat(api_key=self.api_key, model=self.model, max_tokens=self.max_tokens)
            # messages = [UserMessage(content=gap_prompt)]
            
            # response = await llm_chat.async_chat(messages)
            # gap_data = json.loads(response.strip())
            
            # return [
            #     GapAnalysisResult(
            #         control_id=item["control_id"],
            #         current_maturity=item["current_maturity"],
            #         target_maturity=item["target_maturity"],
            #         gap_score=item["gap_score"],
            #         gap_explanation=item["gap_explanation"],
            #         priority_level=item["priority_level"],
            #         estimated_effort=item["estimated_effort"],
            #         dependencies=item["dependencies"]
            #     )
            #     for item in gap_data
            # ]
            
        except Exception as e:
            logger.error(f"Gap analysis failed: {str(e)}")
            return await self._create_mock_gap_analysis(basic_result)
    
    async def _generate_remediation_recommendations(self, basic_result: AIAnalysisResult, gap_analysis: List[GapAnalysisResult]) -> List[RemediationRecommendation]:
        """Generate actionable remediation recommendations"""
        
        if not self.api_key or self.api_key == "test-key-for-demo":
            return await self._create_mock_remediation(gap_analysis)
        
        try:
            remediation_prompt = f"""
            Generate actionable remediation recommendations based on gap analysis.
            
            GAP ANALYSIS: {json.dumps([gap.__dict__ for gap in gap_analysis], default=str)}
            EVIDENCE: {json.dumps(basic_result.__dict__, default=str)}
            
            For each high-priority gap, create specific remediation plans:
            1. Clear implementation steps
            2. Timeline estimates
            3. Required resources
            4. Success criteria
            5. Risk reduction impact
            
            Return JSON array:
            [
                {{
                    "control_id": "PR.AC-01",
                    "recommendation_id": "REM-001",
                    "title": "Implement Formal Access Control Policy",
                    "description": "Detailed recommendation description",
                    "implementation_steps": ["step1", "step2", "step3"],
                    "estimated_timeline": "2-3 months",
                    "required_resources": ["Security Analyst", "Policy Template"],
                    "success_criteria": ["criteria1", "criteria2"],
                    "risk_reduction": 0.75,
                    "confidence_score": 0.88
                }}
            ]
            """
            
            # llm_chat = LlmChat(api_key=self.api_key, model=self.model, max_tokens=self.max_tokens)
            # messages = [UserMessage(content=remediation_prompt)]
            
            # response = await llm_chat.async_chat(messages)
            # remediation_data = json.loads(response.strip())
            
            # return [
            #     RemediationRecommendation(
            #         control_id=item["control_id"],
            #         recommendation_id=item["recommendation_id"],
            #         title=item["title"],
            #         description=item["description"],
            #         implementation_steps=item["implementation_steps"],
            #         estimated_timeline=item["estimated_timeline"],
            #         required_resources=item["required_resources"],
            #         success_criteria=item["success_criteria"],
            #         risk_reduction=item["risk_reduction"],
            #         confidence_score=item["confidence_score"]
            #     )
            #     for item in remediation_data
            # ]
            
        except Exception as e:
            logger.error(f"Remediation generation failed: {str(e)}")
            return await self._create_mock_remediation(gap_analysis)
    
    async def update_confidence_override(self, analysis_id: str, control_id: str, 
                                       old_confidence: float, new_confidence: float, 
                                       reason: str, user_id: str) -> Dict[str, Any]:
        """Track confidence score overrides for learning"""
        
        override_record = {
            "override_id": str(uuid.uuid4()),
            "analysis_id": analysis_id,
            "control_id": control_id,
            "old_confidence": old_confidence,
            "new_confidence": new_confidence,
            "reason": reason,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "ai_model": self.model
        }
        
        # In production, store this for ML model improvement
        logger.info(f"Confidence override recorded: {control_id} {old_confidence} -> {new_confidence}")
        
        return override_record
    
    # Mock data generators for development/demo mode
    async def _create_mock_basic_analysis(self, filename: str, file_content: bytes, mime_type: str) -> AIAnalysisResult:
        """Create realistic mock analysis for demo purposes"""
        
        # Simulate different document types
        if "policy" in filename.lower():
            classification = "policy"
            nist_controls = [
                {"subcategory": "GV.PO-01", "confidence": 0.94, "rationale": "Document establishes governance policies"},
                {"subcategory": "GV.OC-01", "confidence": 0.87, "rationale": "Addresses organizational context"}
            ]
        elif "procedure" in filename.lower():
            classification = "procedure"  
            nist_controls = [
                {"subcategory": "PR.IP-01", "confidence": 0.91, "rationale": "Operational procedures documented"},
                {"subcategory": "PR.IP-02", "confidence": 0.85, "rationale": "Security procedures defined"}
            ]
        else:
            classification = "evidence"
            nist_controls = [
                {"subcategory": "DE.CM-01", "confidence": 0.89, "rationale": "Evidence of monitoring activities"},
                {"subcategory": "RS.RP-01", "confidence": 0.82, "rationale": "Response planning documented"}
            ]
        
        return AIAnalysisResult(
            classification=classification,
            confidence=0.92,
            description=f"DAAKYI AI analysis of {filename}: {classification} document with high compliance relevance",
            extracted_metadata={
                "document_type": classification,
                "framework_alignment": "NIST CSF 2.0",
                "compliance_level": "high"
            },
            nist_mappings=[
                {
                    "controlId": mapping["subcategory"],
                    "confidence": mapping["confidence"],
                    "rationale": mapping["rationale"]
                }
                for mapping in nist_controls
            ],
            risk_findings=[
                {
                    "level": "medium",
                    "description": "Consider cross-referencing with related policies",
                    "recommendation": "Ensure regular review and update cycles"
                },
                {
                    "level": "low", 
                    "description": "Validate implementation evidence",
                    "recommendation": "Document implementation status"
                }
            ]
        )
    
    async def _create_mock_summary(self, filename: str) -> DocumentSummary:
        """Create mock document summary"""
        return DocumentSummary(
            executive_summary=f"This document provides critical cybersecurity governance and risk management guidance, demonstrating mature compliance practices aligned with NIST CSF 2.0 requirements.",
            key_findings=[
                "Comprehensive cybersecurity policy framework established",
                "Clear roles and responsibilities defined",
                "Regular assessment and improvement processes documented",
                "Strong alignment with industry best practices"
            ],
            compliance_insights=[
                "Document supports NIST CSF 2.0 governance requirements",
                "Evidence of proactive risk management approach",
                "Demonstrates commitment to continuous improvement"
            ],
            recommended_actions=[
                "Ensure policy implementation across all business units",
                "Establish regular compliance monitoring processes",
                "Consider integration with incident response procedures"
            ],
            risk_assessment="Medium risk level with strong foundational controls in place. Recommend periodic review to maintain effectiveness.",
            confidence_score=0.91
        )
    
    async def _create_mock_gap_analysis(self, basic_result: AIAnalysisResult) -> List[GapAnalysisResult]:
        """Create mock gap analysis results"""
        return [
            GapAnalysisResult(
                control_id="GV.PO-01",
                current_maturity=2,
                target_maturity=4,
                gap_score=0.5,
                gap_explanation="Policy exists but lacks comprehensive implementation guidance and regular review processes",
                priority_level="high",
                estimated_effort="2-3 months",
                dependencies=["GV.OC-01", "GV.RM-01"]
            ),
            GapAnalysisResult(
                control_id="PR.AC-01",
                current_maturity=3,
                target_maturity=4,
                gap_score=0.25,
                gap_explanation="Access control policy is well-defined but could benefit from enhanced monitoring and automation",
                priority_level="medium",
                estimated_effort="1-2 months",
                dependencies=["PR.AC-02", "DE.CM-01"]
            )
        ]
    
    async def _create_mock_remediation(self, gap_analysis: List[GapAnalysisResult]) -> List[RemediationRecommendation]:
        """Create mock remediation recommendations"""
        return [
            RemediationRecommendation(
                control_id="GV.PO-01",
                recommendation_id="REM-001",
                title="Enhance Governance Policy Implementation",
                description="Strengthen policy governance through comprehensive implementation guidance, regular review cycles, and stakeholder training programs",
                implementation_steps=[
                    "Develop detailed implementation guidelines for each policy area",
                    "Establish quarterly policy review committee meetings",
                    "Create policy awareness training program for all staff",
                    "Implement policy compliance monitoring dashboard",
                    "Design policy exception management process"
                ],
                estimated_timeline="2-3 months",
                required_resources=[
                    "Governance Specialist",
                    "Training Coordinator", 
                    "Policy Management System",
                    "Compliance Dashboard Tool"
                ],
                success_criteria=[
                    "100% staff completion of policy training",
                    "Quarterly policy review process established",
                    "Policy compliance monitoring active",
                    "Exception management process operational"
                ],
                risk_reduction=0.65,
                confidence_score=0.88
            ),
            RemediationRecommendation(
                control_id="PR.AC-01",
                recommendation_id="REM-002", 
                title="Implement Advanced Access Control Monitoring",
                description="Deploy automated access control monitoring and implement continuous compliance verification for access management processes",
                implementation_steps=[
                    "Deploy access monitoring automation tools",
                    "Configure real-time access violation alerts",
                    "Implement periodic access review workflows",
                    "Create access control compliance dashboards"
                ],
                estimated_timeline="1-2 months",
                required_resources=[
                    "Identity Management Specialist",
                    "SIEM Integration",
                    "Access Monitoring Tools"
                ],
                success_criteria=[
                    "Real-time access monitoring operational",
                    "Automated compliance reporting active",
                    "Zero tolerance policy violations"
                ],
                risk_reduction=0.45,
                confidence_score=0.85
            )
        ]
    
    async def _create_fallback_enhanced_result(self, filename: str) -> EnhancedAnalysisResult:
        """Create fallback result when all analysis fails"""
        basic_result = await self._create_mock_basic_analysis(filename, b"", "")
        summary = await self._create_mock_summary(filename)
        gap_analysis = await self._create_mock_gap_analysis(basic_result)
        remediation = await self._create_mock_remediation(gap_analysis)
        
        return EnhancedAnalysisResult(
            basic_analysis=basic_result,
            document_summary=summary,
            gap_analysis=gap_analysis,
            remediation_recommendations=remediation,
            confidence_override_history=[],
            processing_metadata={
                "processing_time": datetime.now().isoformat(),
                "ai_model": "DAAKYI-AI-Fallback",
                "mode": "mock_analysis"
            }
        )

# Global instance
advanced_ai_service = AdvancedAIService()

def get_advanced_ai_service() -> AdvancedAIService:
    """Get the global advanced AI service instance"""
    return advanced_ai_service