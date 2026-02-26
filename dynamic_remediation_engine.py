"""
DAAKYI CompaaS - Dynamic Remediation Intelligence Engine
AI-powered contextual recommendations, prioritized remediation plans,
and optimization insights for audit readiness
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)

class RemediationPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class RemediationType(Enum):
    PROCESS_IMPROVEMENT = "process_improvement"
    DOCUMENTATION = "documentation"
    TRAINING = "training"
    TECHNOLOGY = "technology"
    GOVERNANCE = "governance"
    COMPLIANCE = "compliance"

class ResourceType(Enum):
    HUMAN = "human"
    FINANCIAL = "financial"
    TECHNOLOGICAL = "technological"
    EXTERNAL = "external"

@dataclass
class RemediationAction:
    action_id: str
    title: str
    description: str
    type: RemediationType
    priority: RemediationPriority
    estimated_effort_hours: int
    estimated_cost: float
    success_probability: float
    risk_reduction: float
    dependencies: List[str]
    required_resources: Dict[ResourceType, int]
    frameworks_impacted: List[str]
    controls_addressed: List[str]
    due_date: datetime
    assigned_team: List[str]
    created_at: datetime

@dataclass
class ContextualFactor:
    factor_id: str
    name: str
    current_value: float
    optimal_value: float
    impact_weight: float
    context_type: str  # "organizational", "technical", "regulatory", "temporal"
    last_updated: datetime

@dataclass
class OptimizationInsight:
    insight_id: str
    title: str
    description: str
    potential_impact: float
    implementation_complexity: str
    resource_optimization: Dict[str, float]
    timeline_optimization: int  # days saved
    quality_improvement: float
    confidence_score: float

class DynamicRemediationEngine:
    """
    Advanced AI engine for generating contextual remediation recommendations
    and optimized action plans
    """
    
    def __init__(self):
        self.contextual_factors = {}
        self.remediation_templates = {}
        self.optimization_rules = {}
        self._initialize_contextual_factors()
        self._initialize_remediation_templates()
        self._initialize_optimization_rules()
    
    def _initialize_contextual_factors(self):
        """Initialize contextual factors that influence remediation decisions"""
        self.contextual_factors = {
            "team_capacity": ContextualFactor(
                factor_id="team_cap",
                name="Team Capacity",
                current_value=0.75,  # 75% capacity
                optimal_value=0.85,
                impact_weight=0.3,
                context_type="organizational",
                last_updated=datetime.utcnow()
            ),
            "budget_availability": ContextualFactor(
                factor_id="budget_avail",
                name="Budget Availability",
                current_value=0.8,   # 80% of budget available
                optimal_value=1.0,
                impact_weight=0.25,
                context_type="organizational",
                last_updated=datetime.utcnow()
            ),
            "regulatory_pressure": ContextualFactor(
                factor_id="reg_pressure",
                name="Regulatory Pressure",
                current_value=0.9,   # High regulatory pressure
                optimal_value=0.7,   # Moderate is optimal
                impact_weight=0.2,
                context_type="regulatory",
                last_updated=datetime.utcnow()
            ),
            "technical_debt": ContextualFactor(
                factor_id="tech_debt",
                name="Technical Debt Level",
                current_value=0.65,  # Moderate technical debt
                optimal_value=0.3,
                impact_weight=0.15,
                context_type="technical",
                last_updated=datetime.utcnow()
            ),
            "change_readiness": ContextualFactor(
                factor_id="change_ready",
                name="Organizational Change Readiness",
                current_value=0.7,
                optimal_value=0.8,
                impact_weight=0.1,
                context_type="organizational",
                last_updated=datetime.utcnow()
            )
        }
    
    def _initialize_remediation_templates(self):
        """Initialize remediation action templates"""
        self.remediation_templates = {
            "documentation_update": {
                "base_effort_hours": 20,
                "base_cost": 2000,
                "success_probability": 0.9,
                "base_risk_reduction": 0.15,
                "complexity_factors": {
                    "policy": 1.5,
                    "procedure": 1.2,
                    "work_instruction": 1.0
                }
            },
            "process_improvement": {
                "base_effort_hours": 40,
                "base_cost": 5000,
                "success_probability": 0.75,
                "base_risk_reduction": 0.25,
                "complexity_factors": {
                    "cross_functional": 2.0,
                    "single_department": 1.2,
                    "individual": 1.0
                }
            },
            "training_program": {
                "base_effort_hours": 30,
                "base_cost": 3500,
                "success_probability": 0.85,
                "base_risk_reduction": 0.2,
                "complexity_factors": {
                    "organization_wide": 2.5,
                    "department": 1.5,
                    "team": 1.0
                }
            },
            "technology_implementation": {
                "base_effort_hours": 80,
                "base_cost": 15000,
                "success_probability": 0.7,
                "base_risk_reduction": 0.35,
                "complexity_factors": {
                    "enterprise": 3.0,
                    "departmental": 1.8,
                    "individual": 1.0
                }
            },
            "governance_enhancement": {
                "base_effort_hours": 60,
                "base_cost": 8000,
                "success_probability": 0.8,
                "base_risk_reduction": 0.3,
                "complexity_factors": {
                    "board_level": 2.5,
                    "executive": 1.8,
                    "management": 1.2
                }
            }
        }
    
    def _initialize_optimization_rules(self):
        """Initialize optimization rules for intelligent recommendations"""
        self.optimization_rules = {
            "resource_optimization": {
                "parallel_execution": {
                    "condition": lambda actions: len(actions) > 3,
                    "benefit": 0.3,  # 30% time reduction
                    "complexity_increase": 0.2
                },
                "skill_matching": {
                    "condition": lambda context: context.get("team_expertise", 0) > 0.8,
                    "benefit": 0.15,  # 15% efficiency increase
                    "complexity_increase": 0
                },
                "vendor_consolidation": {
                    "condition": lambda actions: sum(1 for a in actions if "external" in str(a)) > 2,
                    "benefit": 0.25,  # 25% cost reduction
                    "complexity_increase": 0.1
                }
            },
            "timeline_optimization": {
                "critical_path": {
                    "condition": lambda actions: len(actions) > 5,
                    "benefit": 0.2,  # 20% time reduction
                    "implementation": "identify_and_optimize_critical_path"
                },
                "quick_wins": {
                    "condition": lambda actions: any(a.estimated_effort_hours < 10 for a in actions),
                    "benefit": 0.1,  # 10% morale boost
                    "implementation": "prioritize_quick_wins"
                }
            },
            "quality_optimization": {
                "expert_review": {
                    "condition": lambda actions: any(a.priority == RemediationPriority.CRITICAL for a in actions),
                    "benefit": 0.25,  # 25% quality improvement
                    "implementation": "require_expert_review"
                },
                "peer_validation": {
                    "condition": lambda actions: len(actions) > 3,
                    "benefit": 0.15,  # 15% quality improvement
                    "implementation": "implement_peer_validation"
                }
            }
        }
    
    def generate_contextual_recommendations(
        self,
        audit_id: str,
        framework: str,
        identified_gaps: List[Dict[str, Any]],
        organizational_context: Dict[str, Any],
        timeline_constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate intelligent, contextual remediation recommendations
        """
        try:
            recommendations = []
            total_estimated_effort = 0
            total_estimated_cost = 0.0
            
            # Analyze organizational context
            context_analysis = self._analyze_organizational_context(organizational_context)
            
            # Generate recommendations for each gap
            for gap in identified_gaps:
                gap_recommendations = self._generate_gap_recommendations(
                    gap, framework, context_analysis, timeline_constraints
                )
                recommendations.extend(gap_recommendations)
                
                # Accumulate totals
                for rec in gap_recommendations:
                    total_estimated_effort += rec.estimated_effort_hours
                    total_estimated_cost += rec.estimated_cost
            
            # Prioritize and optimize recommendations
            prioritized_recommendations = self._prioritize_recommendations(
                recommendations, context_analysis, timeline_constraints
            )
            
            # Generate optimization insights
            optimization_insights = self._generate_optimization_insights(
                prioritized_recommendations, context_analysis
            )
            
            # Create implementation roadmap
            implementation_roadmap = self._create_implementation_roadmap(
                prioritized_recommendations, timeline_constraints
            )
            
            # Calculate success metrics
            success_metrics = self._calculate_success_metrics(prioritized_recommendations)
            
            return {
                "recommendation_id": str(uuid.uuid4()),
                "audit_id": audit_id,
                "framework": framework,
                "generated_at": datetime.utcnow().isoformat(),
                "context_analysis": context_analysis,
                "recommendations": [
                    {
                        "action_id": rec.action_id,
                        "title": rec.title,
                        "description": rec.description,
                        "type": rec.type.value,
                        "priority": rec.priority.value,
                        "estimated_effort_hours": rec.estimated_effort_hours,
                        "estimated_cost": rec.estimated_cost,
                        "success_probability": rec.success_probability,
                        "risk_reduction": rec.risk_reduction,
                        "dependencies": rec.dependencies,
                        "required_resources": {k.value: v for k, v in rec.required_resources.items()},
                        "frameworks_impacted": rec.frameworks_impacted,
                        "controls_addressed": rec.controls_addressed,
                        "due_date": rec.due_date.isoformat(),
                        "assigned_team": rec.assigned_team
                    }
                    for rec in prioritized_recommendations
                ],
                "optimization_insights": [
                    {
                        "insight_id": insight.insight_id,
                        "title": insight.title,
                        "description": insight.description,
                        "potential_impact": insight.potential_impact,
                        "implementation_complexity": insight.implementation_complexity,
                        "resource_optimization": insight.resource_optimization,
                        "timeline_optimization": insight.timeline_optimization,
                        "quality_improvement": insight.quality_improvement,
                        "confidence_score": insight.confidence_score
                    }
                    for insight in optimization_insights
                ],
                "implementation_roadmap": implementation_roadmap,
                "success_metrics": success_metrics,
                "totals": {
                    "total_actions": len(prioritized_recommendations),
                    "total_estimated_effort_hours": total_estimated_effort,
                    "total_estimated_cost": total_estimated_cost,
                    "total_risk_reduction": sum(rec.risk_reduction for rec in prioritized_recommendations),
                    "average_success_probability": sum(rec.success_probability for rec in prioritized_recommendations) / max(len(prioritized_recommendations), 1)
                }
            }
        
        except Exception as e:
            logger.error(f"Error generating contextual recommendations: {str(e)}")
            raise
    
    def _analyze_organizational_context(self, org_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze organizational context to inform recommendations"""
        try:
            # Extract key organizational factors
            team_size = org_context.get("team_size", 10)
            budget_constraints = org_context.get("budget_constraints", "moderate")
            industry_type = org_context.get("industry", "technology")
            maturity_level = org_context.get("maturity_level", "developing")
            change_tolerance = org_context.get("change_tolerance", "moderate")
            
            # Calculate context scores
            context_scores = {}
            
            # Team capacity assessment
            if team_size < 5:
                context_scores["team_capacity"] = 0.6  # Limited capacity
            elif team_size < 15:
                context_scores["team_capacity"] = 0.8  # Good capacity
            else:
                context_scores["team_capacity"] = 0.9  # High capacity
            
            # Budget flexibility
            budget_flexibility = {
                "tight": 0.4,
                "moderate": 0.7,
                "flexible": 0.9
            }
            context_scores["budget_flexibility"] = budget_flexibility.get(budget_constraints, 0.7)
            
            # Industry complexity
            industry_complexity = {
                "financial": 0.9,
                "healthcare": 0.85,
                "technology": 0.8,
                "manufacturing": 0.7,
                "retail": 0.6
            }
            context_scores["industry_complexity"] = industry_complexity.get(industry_type, 0.75)
            
            # Maturity assessment
            maturity_scores = {
                "initial": 0.3,
                "developing": 0.5,
                "managed": 0.7,
                "optimized": 0.9
            }
            context_scores["maturity_level"] = maturity_scores.get(maturity_level, 0.5)
            
            # Change readiness
            change_readiness_scores = {
                "low": 0.4,
                "moderate": 0.7,
                "high": 0.9
            }
            context_scores["change_readiness"] = change_readiness_scores.get(change_tolerance, 0.7)
            
            # Generate context insights
            insights = []
            if context_scores["team_capacity"] < 0.7:
                insights.append("Limited team capacity may require external resources or extended timelines")
            if context_scores["budget_flexibility"] < 0.6:
                insights.append("Budget constraints suggest prioritizing low-cost, high-impact actions")
            if context_scores["maturity_level"] < 0.6:
                insights.append("Lower maturity level indicates need for foundational improvements first")
            if context_scores["change_readiness"] < 0.6:
                insights.append("Change management support will be critical for successful implementation")
            
            return {
                "context_scores": context_scores,
                "insights": insights,
                "overall_readiness": sum(context_scores.values()) / len(context_scores),
                "primary_constraints": [k for k, v in context_scores.items() if v < 0.6],
                "organizational_strengths": [k for k, v in context_scores.items() if v > 0.8]
            }
        
        except Exception as e:
            logger.error(f"Error analyzing organizational context: {str(e)}")
            return {"context_scores": {}, "insights": [], "overall_readiness": 0.5}
    
    def _generate_gap_recommendations(
        self,
        gap: Dict[str, Any],
        framework: str,
        context_analysis: Dict[str, Any],
        timeline_constraints: Dict[str, Any]
    ) -> List[RemediationAction]:
        """Generate specific recommendations for a identified gap"""
        try:
            recommendations = []
            gap_type = gap.get("type", "general")
            gap_severity = gap.get("severity", "medium")
            affected_controls = gap.get("controls", [])
            
            # Determine appropriate remediation types based on gap
            remediation_types = self._determine_remediation_types(gap_type, gap_severity)
            
            for rem_type in remediation_types:
                action = self._create_remediation_action(
                    gap, rem_type, framework, context_analysis, timeline_constraints, affected_controls
                )
                if action:
                    recommendations.append(action)
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error generating gap recommendations: {str(e)}")
            return []
    
    def _determine_remediation_types(self, gap_type: str, severity: str) -> List[str]:
        """Determine appropriate remediation types for a gap"""
        type_mapping = {
            "documentation": ["documentation_update"],
            "process": ["process_improvement", "documentation_update"],
            "training": ["training_program"],
            "technology": ["technology_implementation", "process_improvement"],
            "governance": ["governance_enhancement", "process_improvement"],
            "compliance": ["documentation_update", "process_improvement", "training_program"]
        }
        
        base_types = type_mapping.get(gap_type, ["process_improvement"])
        
        # Add additional types based on severity
        if severity == "critical":
            if "governance_enhancement" not in base_types:
                base_types.append("governance_enhancement")
        elif severity == "high":
            if "training_program" not in base_types:
                base_types.append("training_program")
        
        return base_types
    
    def _create_remediation_action(
        self,
        gap: Dict[str, Any],
        remediation_type: str,
        framework: str,
        context_analysis: Dict[str, Any],
        timeline_constraints: Dict[str, Any],
        affected_controls: List[str]
    ) -> Optional[RemediationAction]:
        """Create a specific remediation action"""
        try:
            template = self.remediation_templates.get(remediation_type)
            if not template:
                return None
            
            gap_severity = gap.get("severity", "medium")
            gap_description = gap.get("description", "General compliance gap")
            
            # Calculate complexity multiplier
            complexity = gap.get("complexity", "single_department")
            complexity_multiplier = template["complexity_factors"].get(complexity, 1.0)
            
            # Adjust for organizational context
            context_multiplier = self._calculate_context_multiplier(
                context_analysis, remediation_type
            )
            
            # Calculate estimates
            estimated_effort = int(template["base_effort_hours"] * complexity_multiplier * context_multiplier)
            estimated_cost = template["base_cost"] * complexity_multiplier * context_multiplier
            
            # Determine priority
            priority = self._determine_action_priority(gap_severity, remediation_type, context_analysis)
            
            # Calculate due date
            days_to_add = max(7, estimated_effort // 8)  # Assume 8 hours per day
            due_date = datetime.utcnow() + timedelta(days=days_to_add)
            
            # Adjust for timeline constraints
            if timeline_constraints.get("aggressive", False):
                due_date = due_date - timedelta(days=max(1, days_to_add // 4))
            
            # Determine required resources
            required_resources = self._calculate_required_resources(
                remediation_type, estimated_effort, estimated_cost
            )
            
            # Generate dependencies
            dependencies = self._identify_dependencies(gap, remediation_type, affected_controls)
            
            return RemediationAction(
                action_id=str(uuid.uuid4()),
                title=f"{remediation_type.replace('_', ' ').title()}: {gap.get('title', 'Compliance Gap')}",
                description=f"Address {gap_description} through {remediation_type.replace('_', ' ')}",
                type=RemediationType(remediation_type),
                priority=priority,
                estimated_effort_hours=estimated_effort,
                estimated_cost=estimated_cost,
                success_probability=template["success_probability"] * context_analysis.get("overall_readiness", 0.7),
                risk_reduction=template["base_risk_reduction"] * (1.2 if gap_severity == "critical" else 1.0),
                dependencies=dependencies,
                required_resources=required_resources,
                frameworks_impacted=[framework],
                controls_addressed=affected_controls,
                due_date=due_date,
                assigned_team=gap.get("assigned_team", ["TBD"]),
                created_at=datetime.utcnow()
            )
        
        except Exception as e:
            logger.error(f"Error creating remediation action: {str(e)}")
            return None
    
    def _calculate_context_multiplier(self, context_analysis: Dict[str, Any], remediation_type: str) -> float:
        """Calculate context-based multiplier for effort and cost"""
        base_multiplier = 1.0
        context_scores = context_analysis.get("context_scores", {})
        
        # Adjust based on team capacity
        team_capacity = context_scores.get("team_capacity", 0.7)
        if team_capacity < 0.6:
            base_multiplier *= 1.3  # 30% more effort needed
        elif team_capacity > 0.8:
            base_multiplier *= 0.9   # 10% less effort needed
        
        # Adjust based on maturity level
        maturity = context_scores.get("maturity_level", 0.5)
        if maturity < 0.5:
            base_multiplier *= 1.2   # 20% more effort for low maturity
        elif maturity > 0.8:
            base_multiplier *= 0.85  # 15% less effort for high maturity
        
        # Type-specific adjustments
        if remediation_type == "technology_implementation":
            tech_readiness = context_scores.get("industry_complexity", 0.75)
            base_multiplier *= (2.0 - tech_readiness)  # Higher complexity = more effort
        
        return base_multiplier
    
    def _determine_action_priority(
        self, 
        gap_severity: str, 
        remediation_type: str, 
        context_analysis: Dict[str, Any]
    ) -> RemediationPriority:
        """Determine priority for remediation action"""
        base_priority_map = {
            "critical": RemediationPriority.CRITICAL,
            "high": RemediationPriority.HIGH,
            "medium": RemediationPriority.MEDIUM,
            "low": RemediationPriority.LOW
        }
        
        base_priority = base_priority_map.get(gap_severity, RemediationPriority.MEDIUM)
        
        # Adjust based on remediation type
        high_impact_types = ["governance_enhancement", "technology_implementation"]
        if remediation_type in high_impact_types and base_priority == RemediationPriority.MEDIUM:
            base_priority = RemediationPriority.HIGH
        
        # Adjust based on organizational context
        constraints = context_analysis.get("primary_constraints", [])
        if len(constraints) > 2 and base_priority == RemediationPriority.HIGH:
            base_priority = RemediationPriority.MEDIUM  # Downgrade due to constraints
        
        return base_priority
    
    def _calculate_required_resources(
        self, 
        remediation_type: str, 
        effort_hours: int, 
        cost: float
    ) -> Dict[ResourceType, int]:
        """Calculate required resources for remediation action"""
        resources = {}
        
        # Human resources (person-days)
        resources[ResourceType.HUMAN] = max(1, effort_hours // 8)
        
        # Financial resources (cost in thousands)
        resources[ResourceType.FINANCIAL] = int(cost // 1000) + 1
        
        # Technology-specific resources
        if remediation_type == "technology_implementation":
            resources[ResourceType.TECHNOLOGICAL] = max(1, effort_hours // 40)
        
        # External resources for complex implementations
        if effort_hours > 100 or cost > 10000:
            resources[ResourceType.EXTERNAL] = 1
        
        return resources
    
    def _identify_dependencies(
        self, 
        gap: Dict[str, Any], 
        remediation_type: str, 
        affected_controls: List[str]
    ) -> List[str]:
        """Identify dependencies for remediation action"""
        dependencies = []
        
        # Add gap-specific dependencies
        if gap.get("dependencies"):
            dependencies.extend(gap["dependencies"])
        
        # Add type-specific dependencies
        if remediation_type == "technology_implementation":
            dependencies.append("governance_approval")
            dependencies.append("budget_approval")
        elif remediation_type == "process_improvement":
            dependencies.append("stakeholder_alignment")
        
        # Add control-based dependencies
        if len(affected_controls) > 3:
            dependencies.append("coordination_planning")
        
        return dependencies
    
    def _prioritize_recommendations(
        self, 
        recommendations: List[RemediationAction], 
        context_analysis: Dict[str, Any],
        timeline_constraints: Dict[str, Any]
    ) -> List[RemediationAction]:
        """Prioritize and optimize recommendations"""
        try:
            # Create scoring function
            def calculate_priority_score(action: RemediationAction) -> float:
                score = 0.0
                
                # Priority weight
                priority_weights = {
                    RemediationPriority.CRITICAL: 100,
                    RemediationPriority.HIGH: 75,
                    RemediationPriority.MEDIUM: 50,
                    RemediationPriority.LOW: 25
                }
                score += priority_weights.get(action.priority, 50)
                
                # Risk reduction weight
                score += action.risk_reduction * 100
                
                # Success probability weight
                score += action.success_probability * 50
                
                # Effort efficiency (impact per hour)
                if action.estimated_effort_hours > 0:
                    efficiency = action.risk_reduction / (action.estimated_effort_hours / 40)  # per week
                    score += efficiency * 20
                
                # Cost efficiency (impact per dollar)
                if action.estimated_cost > 0:
                    cost_efficiency = action.risk_reduction / (action.estimated_cost / 1000)  # per $1k
                    score += cost_efficiency * 10
                
                # Context adjustment
                overall_readiness = context_analysis.get("overall_readiness", 0.7)
                score *= overall_readiness
                
                return score
            
            # Sort by priority score
            recommendations.sort(key=calculate_priority_score, reverse=True)
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error prioritizing recommendations: {str(e)}")
            return recommendations
    
    def _generate_optimization_insights(
        self, 
        recommendations: List[RemediationAction], 
        context_analysis: Dict[str, Any]
    ) -> List[OptimizationInsight]:
        """Generate optimization insights for the remediation plan"""
        try:
            insights = []
            
            # Resource optimization insights
            resource_insight = self._analyze_resource_optimization(recommendations)
            if resource_insight:
                insights.append(resource_insight)
            
            # Timeline optimization insights
            timeline_insight = self._analyze_timeline_optimization(recommendations)
            if timeline_insight:
                insights.append(timeline_insight)
            
            # Quality optimization insights
            quality_insight = self._analyze_quality_optimization(recommendations)
            if quality_insight:
                insights.append(quality_insight)
            
            # Cost optimization insights
            cost_insight = self._analyze_cost_optimization(recommendations, context_analysis)
            if cost_insight:
                insights.append(cost_insight)
            
            return insights
        
        except Exception as e:
            logger.error(f"Error generating optimization insights: {str(e)}")
            return []
    
    def _analyze_resource_optimization(self, recommendations: List[RemediationAction]) -> Optional[OptimizationInsight]:
        """Analyze resource optimization opportunities"""
        try:
            if len(recommendations) < 3:
                return None
            
            # Analyze resource overlap
            human_resources = sum(rec.required_resources.get(ResourceType.HUMAN, 0) for rec in recommendations)
            
            # Check for potential parallelization
            parallel_candidates = [rec for rec in recommendations if not rec.dependencies]
            
            if len(parallel_candidates) > 2:
                time_saved = min(30, len(parallel_candidates) * 5)  # Up to 30 days saved
                resource_optimization = {"human": 0.8, "timeline": 0.7}  # 20% resource efficiency, 30% time efficiency
                
                return OptimizationInsight(
                    insight_id=str(uuid.uuid4()),
                    title="Parallel Execution Opportunity",
                    description=f"Execute {len(parallel_candidates)} independent actions in parallel to optimize timeline and resource utilization",
                    potential_impact=0.25,
                    implementation_complexity="moderate",
                    resource_optimization=resource_optimization,
                    timeline_optimization=time_saved,
                    quality_improvement=0.1,
                    confidence_score=0.8
                )
            
            return None
        
        except Exception as e:
            logger.error(f"Error analyzing resource optimization: {str(e)}")
            return None
    
    def _analyze_timeline_optimization(self, recommendations: List[RemediationAction]) -> Optional[OptimizationInsight]:
        """Analyze timeline optimization opportunities"""
        try:
            # Look for quick wins
            quick_wins = [rec for rec in recommendations if rec.estimated_effort_hours < 20 and rec.risk_reduction > 0.1]
            
            if len(quick_wins) >= 2:
                return OptimizationInsight(
                    insight_id=str(uuid.uuid4()),
                    title="Quick Wins Strategy",
                    description=f"Prioritize {len(quick_wins)} quick wins to build momentum and demonstrate early progress",
                    potential_impact=0.15,
                    implementation_complexity="low",
                    resource_optimization={"morale": 1.2, "momentum": 1.3},
                    timeline_optimization=7,  # 1 week of momentum gain
                    quality_improvement=0.1,
                    confidence_score=0.9
                )
            
            return None
        
        except Exception as e:
            logger.error(f"Error analyzing timeline optimization: {str(e)}")
            return None
    
    def _analyze_quality_optimization(self, recommendations: List[RemediationAction]) -> Optional[OptimizationInsight]:
        """Analyze quality optimization opportunities"""
        try:
            critical_actions = [rec for rec in recommendations if rec.priority == RemediationPriority.CRITICAL]
            
            if len(critical_actions) > 0:
                return OptimizationInsight(
                    insight_id=str(uuid.uuid4()),
                    title="Expert Review Process",
                    description=f"Implement expert review for {len(critical_actions)} critical actions to ensure quality and reduce rework risk",
                    potential_impact=0.2,
                    implementation_complexity="low",
                    resource_optimization={"quality": 1.25, "rework_risk": 0.3},
                    timeline_optimization=0,  # No timeline impact
                    quality_improvement=0.25,
                    confidence_score=0.85
                )
            
            return None
        
        except Exception as e:
            logger.error(f"Error analyzing quality optimization: {str(e)}")
            return None
    
    def _analyze_cost_optimization(
        self, 
        recommendations: List[RemediationAction], 
        context_analysis: Dict[str, Any]
    ) -> Optional[OptimizationInsight]:
        """Analyze cost optimization opportunities"""
        try:
            total_cost = sum(rec.estimated_cost for rec in recommendations)
            budget_flexibility = context_analysis.get("context_scores", {}).get("budget_flexibility", 0.7)
            
            if budget_flexibility < 0.6 and total_cost > 50000:
                # Suggest phased approach
                return OptimizationInsight(
                    insight_id=str(uuid.uuid4()),
                    title="Phased Implementation Strategy",
                    description="Implement remediation in phases to spread costs and align with budget constraints",
                    potential_impact=0.1,
                    implementation_complexity="moderate",
                    resource_optimization={"budget_alignment": 1.3, "cash_flow": 1.2},
                    timeline_optimization=-14,  # May add 2 weeks due to phasing
                    quality_improvement=0.05,
                    confidence_score=0.75
                )
            
            return None
        
        except Exception as e:
            logger.error(f"Error analyzing cost optimization: {str(e)}")
            return None
    
    def _create_implementation_roadmap(
        self, 
        recommendations: List[RemediationAction], 
        timeline_constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create implementation roadmap with phases and milestones"""
        try:
            # Group actions by priority and dependencies
            phases = []
            current_phase = []
            phase_number = 1
            
            remaining_actions = recommendations.copy()
            
            while remaining_actions:
                # Find actions with no unfulfilled dependencies
                ready_actions = [
                    action for action in remaining_actions
                    if not action.dependencies or all(
                        dep in [completed.action_id for completed in recommendations if completed not in remaining_actions]
                        for dep in action.dependencies
                    )
                ]
                
                if not ready_actions:
                    # Break circular dependencies by taking highest priority action
                    ready_actions = [max(remaining_actions, key=lambda x: x.priority.value)]
                
                # Add to current phase
                current_phase.extend(ready_actions)
                
                # Remove from remaining
                for action in ready_actions:
                    remaining_actions.remove(action)
                
                # Check if phase is complete (either max actions or no more ready actions)
                if len(current_phase) >= 5 or not remaining_actions:
                    phases.append({
                        "phase_number": phase_number,
                        "phase_name": f"Phase {phase_number}",
                        "actions": [action.action_id for action in current_phase],
                        "estimated_duration_days": max(action.estimated_effort_hours // 8 for action in current_phase) if current_phase else 0,
                        "total_cost": sum(action.estimated_cost for action in current_phase),
                        "key_deliverables": [action.title for action in current_phase[:3]]  # Top 3
                    })
                    current_phase = []
                    phase_number += 1
            
            # Calculate overall timeline
            total_duration = sum(phase["estimated_duration_days"] for phase in phases)
            
            # Create milestones
            milestones = []
            cumulative_days = 0
            for i, phase in enumerate(phases):
                cumulative_days += phase["estimated_duration_days"]
                milestones.append({
                    "milestone_name": f"Phase {phase['phase_number']} Complete",
                    "target_date": (datetime.utcnow() + timedelta(days=cumulative_days)).isoformat(),
                    "deliverables": phase["key_deliverables"],
                    "success_criteria": [f"All {len(phase['actions'])} phase actions completed"]
                })
            
            return {
                "roadmap_id": str(uuid.uuid4()),
                "total_phases": len(phases),
                "total_duration_days": total_duration,
                "start_date": datetime.utcnow().isoformat(),
                "target_completion": (datetime.utcnow() + timedelta(days=total_duration)).isoformat(),
                "phases": phases,
                "milestones": milestones,
                "critical_path": [phase["phase_number"] for phase in phases if any(
                    action.priority == RemediationPriority.CRITICAL 
                    for action in recommendations 
                    if action.action_id in phase["actions"]
                )]
            }
        
        except Exception as e:
            logger.error(f"Error creating implementation roadmap: {str(e)}")
            return {"error": "Failed to create roadmap", "phases": [], "milestones": []}
    
    def _calculate_success_metrics(self, recommendations: List[RemediationAction]) -> Dict[str, Any]:
        """Calculate success metrics for the remediation plan"""
        try:
            if not recommendations:
                return {"overall_success_probability": 0.0}
            
            # Overall success probability (compound probability)
            individual_probabilities = [rec.success_probability for rec in recommendations]
            overall_success = 1.0
            for prob in individual_probabilities:
                overall_success *= prob
            
            # Total risk reduction
            total_risk_reduction = sum(rec.risk_reduction for rec in recommendations)
            
            # Resource efficiency
            total_effort = sum(rec.estimated_effort_hours for rec in recommendations)
            effort_per_risk_reduction = total_effort / max(total_risk_reduction, 0.1)
            
            # Cost efficiency
            total_cost = sum(rec.estimated_cost for rec in recommendations)
            cost_per_risk_reduction = total_cost / max(total_risk_reduction, 0.1)
            
            # Priority distribution
            priority_distribution = {}
            for priority in RemediationPriority:
                count = sum(1 for rec in recommendations if rec.priority == priority)
                priority_distribution[priority.value] = count
            
            return {
                "overall_success_probability": round(overall_success, 3),
                "total_risk_reduction": round(total_risk_reduction, 3),
                "resource_efficiency": round(1 / effort_per_risk_reduction * 1000, 2),  # Risk reduction per 1000 hours
                "cost_efficiency": round(1 / cost_per_risk_reduction * 10000, 2),  # Risk reduction per $10k
                "priority_distribution": priority_distribution,
                "average_success_probability": round(sum(individual_probabilities) / len(individual_probabilities), 3),
                "total_actions": len(recommendations),
                "estimated_completion_weeks": max(1, total_effort // 40)  # Assuming 40 hours per week
            }
        
        except Exception as e:
            logger.error(f"Error calculating success metrics: {str(e)}")
            return {"overall_success_probability": 0.0, "error": "Calculation failed"}


# Initialize global remediation engine instance
dynamic_remediation_engine = DynamicRemediationEngine()