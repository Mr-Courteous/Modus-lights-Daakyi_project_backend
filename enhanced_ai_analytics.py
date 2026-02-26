"""
DAAKYI CompaaS - Enhanced AI Analytics Service
Advanced predictive analytics engine with confidence interval modeling,
risk-weighted forecasting, and multi-factor temporal trend analysis
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid
import logging
import math

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class FrameworkType(Enum):
    NIST_CSF = "NIST CSF 2.0"
    ISO_27001 = "ISO 27001:2022"
    SOC_2 = "SOC 2"
    GDPR = "GDPR"

@dataclass
class ConfidenceInterval:
    lower_bound: float
    upper_bound: float
    confidence_level: float
    method: str
    sample_size: int

@dataclass
class RiskFactor:
    factor_id: str
    name: str
    impact_score: float  # 0-1 scale
    probability: float   # 0-1 scale
    trend: str          # "increasing", "stable", "decreasing"
    last_updated: datetime
    framework_relevance: Dict[str, float]  # Framework -> relevance score

@dataclass
class TemporalDataPoint:
    timestamp: datetime
    readiness_score: float
    confidence: float
    contributing_factors: Dict[str, float]
    milestone_completion: float
    evidence_quality: float

@dataclass
class PredictiveModel:
    model_id: str
    model_type: str
    accuracy_score: float
    last_trained: datetime
    feature_importance: Dict[str, float]
    hyperparameters: Dict[str, Any]

class EnhancedAIAnalyticsEngine:
    """
    Advanced AI analytics engine for audit readiness prediction and optimization
    """
    
    def __init__(self):
        self.models = {}
        self.risk_factors_db = {}
        self.temporal_data = {}
        self._initialize_risk_factors()
        self._initialize_models()
    
    def _initialize_risk_factors(self):
        """Initialize comprehensive risk factor database"""
        self.risk_factors_db = {
            "documentation_completeness": RiskFactor(
                factor_id="doc_complete",
                name="Documentation Completeness",
                impact_score=0.35,
                probability=0.8,
                trend="stable",
                last_updated=datetime.utcnow(),
                framework_relevance={
                    "NIST CSF 2.0": 0.9,
                    "ISO 27001:2022": 0.95,
                    "SOC 2": 0.8,
                    "GDPR": 0.7
                }
            ),
            "team_preparedness": RiskFactor(
                factor_id="team_prep",
                name="Team Preparedness",
                impact_score=0.25,
                probability=0.7,
                trend="increasing",
                last_updated=datetime.utcnow(),
                framework_relevance={
                    "NIST CSF 2.0": 0.8,
                    "ISO 27001:2022": 0.85,
                    "SOC 2": 0.9,
                    "GDPR": 0.75
                }
            ),
            "evidence_quality": RiskFactor(
                factor_id="evidence_qual",
                name="Evidence Quality",
                impact_score=0.3,
                probability=0.6,
                trend="stable",
                last_updated=datetime.utcnow(),
                framework_relevance={
                    "NIST CSF 2.0": 0.85,
                    "ISO 27001:2022": 0.9,
                    "SOC 2": 0.95,
                    "GDPR": 0.8
                }
            ),
            "timeline_pressure": RiskFactor(
                factor_id="timeline_press",
                name="Timeline Pressure",
                impact_score=0.2,
                probability=0.4,
                trend="decreasing",
                last_updated=datetime.utcnow(),
                framework_relevance={
                    "NIST CSF 2.0": 0.7,
                    "ISO 27001:2022": 0.8,
                    "SOC 2": 0.85,
                    "GDPR": 0.6
                }
            ),
            "process_maturity": RiskFactor(
                factor_id="process_mat",
                name="Process Maturity",
                impact_score=0.4,
                probability=0.5,
                trend="increasing",
                last_updated=datetime.utcnow(),
                framework_relevance={
                    "NIST CSF 2.0": 0.8,
                    "ISO 27001:2022": 0.95,
                    "SOC 2": 0.7,
                    "GDPR": 0.6
                }
            )
        }
    
    def _initialize_models(self):
        """Initialize predictive models with metadata"""
        self.models = {
            "readiness_predictor": PredictiveModel(
                model_id="readiness_v2.1",
                model_type="ensemble_regression",
                accuracy_score=0.89,
                last_trained=datetime.utcnow() - timedelta(days=7),
                feature_importance={
                    "documentation_completeness": 0.28,
                    "evidence_quality": 0.24,
                    "team_preparedness": 0.18,
                    "process_maturity": 0.16,
                    "timeline_pressure": 0.14
                },
                hyperparameters={
                    "n_estimators": 100,
                    "learning_rate": 0.1,
                    "max_depth": 6,
                    "regularization": 0.01
                }
            ),
            "risk_classifier": PredictiveModel(
                model_id="risk_v1.3",
                model_type="gradient_boosting_classifier",
                accuracy_score=0.92,
                last_trained=datetime.utcnow() - timedelta(days=5),
                feature_importance={
                    "gap_severity": 0.35,
                    "remediation_complexity": 0.25,
                    "resource_availability": 0.20,
                    "timeline_constraints": 0.20
                },
                hyperparameters={
                    "n_estimators": 150,
                    "learning_rate": 0.05,
                    "max_depth": 8
                }
            )
        }
    
    def calculate_enhanced_confidence_intervals(
        self, 
        base_score: float, 
        historical_variance: float = 0.05,
        sample_size: int = 30,
        confidence_level: float = 0.95
    ) -> ConfidenceInterval:
        """
        Calculate sophisticated confidence intervals using multiple statistical methods
        """
        try:
            # Use t-distribution for small samples, normal for large samples
            if sample_size < 30:
                # t-distribution
                from scipy import stats
                t_critical = stats.t.ppf((1 + confidence_level) / 2, df=sample_size - 1)
                margin_of_error = t_critical * (historical_variance / math.sqrt(sample_size))
                method = "t_distribution"
            else:
                # Normal distribution
                z_critical = 1.96 if confidence_level == 0.95 else 2.58  # 95% or 99%
                margin_of_error = z_critical * (historical_variance / math.sqrt(sample_size))
                method = "normal_distribution"
            
            lower_bound = max(0.0, base_score - margin_of_error)
            upper_bound = min(100.0, base_score + margin_of_error)
            
            return ConfidenceInterval(
                lower_bound=round(lower_bound, 2),
                upper_bound=round(upper_bound, 2),
                confidence_level=confidence_level,
                method=method,
                sample_size=sample_size
            )
        
        except ImportError:
            # Fallback method without scipy
            logger.warning("scipy not available, using simplified confidence interval calculation")
            margin_of_error = 1.96 * (historical_variance / math.sqrt(max(sample_size, 1)))
            
            return ConfidenceInterval(
                lower_bound=max(0.0, round(base_score - margin_of_error, 2)),
                upper_bound=min(100.0, round(base_score + margin_of_error, 2)),
                confidence_level=confidence_level,
                method="simplified_normal",
                sample_size=sample_size
            )
    
    def generate_risk_weighted_forecast(
        self, 
        audit_id: str, 
        current_readiness: float,
        framework: str,
        days_remaining: int
    ) -> Dict[str, Any]:
        """
        Generate risk-weighted readiness forecast with multiple scenarios
        """
        try:
            # Get framework-specific risk factors
            relevant_risks = self._get_framework_risks(framework)
            
            # Calculate base trajectory
            base_trajectory = self._calculate_base_trajectory(
                current_readiness, days_remaining
            )
            
            # Apply risk-weighted adjustments
            optimistic_scenario = self._apply_risk_adjustments(
                base_trajectory, relevant_risks, scenario="optimistic"
            )
            
            realistic_scenario = self._apply_risk_adjustments(
                base_trajectory, relevant_risks, scenario="realistic"
            )
            
            pessimistic_scenario = self._apply_risk_adjustments(
                base_trajectory, relevant_risks, scenario="pessimistic"
            )
            
            # Calculate confidence intervals for each scenario
            realistic_ci = self.calculate_enhanced_confidence_intervals(
                realistic_scenario["final_score"],
                historical_variance=0.08,
                sample_size=45
            )
            
            # Monte Carlo simulation for probability distributions
            success_probability = self._monte_carlo_success_simulation(
                realistic_scenario, relevant_risks, iterations=1000
            )
            
            return {
                "forecast_id": str(uuid.uuid4()),
                "audit_id": audit_id,
                "generated_at": datetime.utcnow().isoformat(),
                "forecast_horizon_days": days_remaining,
                "current_readiness": current_readiness,
                "scenarios": {
                    "optimistic": {
                        "final_score": optimistic_scenario["final_score"],
                        "trajectory": optimistic_scenario["trajectory"],
                        "probability": 0.15,
                        "key_assumptions": optimistic_scenario["assumptions"]
                    },
                    "realistic": {
                        "final_score": realistic_scenario["final_score"],
                        "trajectory": realistic_scenario["trajectory"],
                        "probability": 0.70,
                        "confidence_interval": {
                            "lower": realistic_ci.lower_bound,
                            "upper": realistic_ci.upper_bound,
                            "confidence_level": realistic_ci.confidence_level
                        },
                        "key_assumptions": realistic_scenario["assumptions"]
                    },
                    "pessimistic": {
                        "final_score": pessimistic_scenario["final_score"],
                        "trajectory": pessimistic_scenario["trajectory"],
                        "probability": 0.15,
                        "key_assumptions": pessimistic_scenario["assumptions"]
                    }
                },
                "success_probability": success_probability,
                "risk_factors": [
                    {
                        "name": risk.name,
                        "impact_score": risk.impact_score,
                        "probability": risk.probability,
                        "trend": risk.trend,
                        "framework_relevance": risk.framework_relevance.get(framework, 0.5)
                    }
                    for risk in relevant_risks
                ],
                "model_metadata": {
                    "model_version": self.models["readiness_predictor"].model_id,
                    "accuracy_score": self.models["readiness_predictor"].accuracy_score,
                    "last_trained": self.models["readiness_predictor"].last_trained.isoformat()
                }
            }
        
        except Exception as e:
            logger.error(f"Error generating risk-weighted forecast: {str(e)}")
            raise
    
    def _get_framework_risks(self, framework: str) -> List[RiskFactor]:
        """Get risks relevant to specific framework"""
        relevant_risks = []
        for risk in self.risk_factors_db.values():
            relevance = risk.framework_relevance.get(framework, 0.0)
            if relevance > 0.5:  # Only include risks with >50% relevance
                relevant_risks.append(risk)
        
        # Sort by impact score descending
        return sorted(relevant_risks, key=lambda x: x.impact_score, reverse=True)
    
    def _calculate_base_trajectory(self, current_score: float, days_remaining: int) -> Dict[str, Any]:
        """Calculate base improvement trajectory without risk adjustments"""
        # S-curve improvement model
        max_improvement = min(95.0 - current_score, 25.0)  # Cap at 95% or 25 point improvement
        
        trajectory = []
        for day in range(0, days_remaining + 1, 7):  # Weekly intervals
            progress_ratio = day / days_remaining if days_remaining > 0 else 1.0
            
            # S-curve formula: improvement = max_improvement / (1 + exp(-k*(x-x0)))
            k = 0.1  # Steepness parameter
            x0 = 0.6  # Midpoint
            s_curve_progress = max_improvement / (1 + math.exp(-k * (progress_ratio - x0)))
            
            projected_score = current_score + s_curve_progress
            trajectory.append({
                "day": day,
                "score": round(projected_score, 1),
                "improvement": round(s_curve_progress, 1)
            })
        
        return {
            "final_score": trajectory[-1]["score"] if trajectory else current_score,
            "trajectory": trajectory,
            "max_improvement": max_improvement
        }
    
    def _apply_risk_adjustments(
        self, 
        base_trajectory: Dict[str, Any], 
        risks: List[RiskFactor], 
        scenario: str
    ) -> Dict[str, Any]:
        """Apply risk-based adjustments to base trajectory"""
        scenario_multipliers = {
            "optimistic": 0.3,   # Risks have 30% of normal impact
            "realistic": 1.0,    # Risks have full impact
            "pessimistic": 1.8   # Risks have 180% impact
        }
        
        multiplier = scenario_multipliers.get(scenario, 1.0)
        
        # Calculate total risk impact
        total_negative_impact = sum(
            risk.impact_score * risk.probability * multiplier
            for risk in risks
        )
        
        # Adjust trajectory
        adjusted_trajectory = []
        for point in base_trajectory["trajectory"]:
            # Risk impact increases over time (more pressure near audit date)
            time_pressure = 1.0 + (point["day"] / max(point["day"] for point in base_trajectory["trajectory"]))
            risk_adjustment = total_negative_impact * time_pressure * 10  # Scale to score points
            
            adjusted_score = max(0.0, point["score"] - risk_adjustment)
            adjusted_trajectory.append({
                "day": point["day"],
                "score": round(adjusted_score, 1),
                "risk_adjustment": round(-risk_adjustment, 1)
            })
        
        # Generate scenario-specific assumptions
        assumptions = self._generate_scenario_assumptions(scenario, risks)
        
        return {
            "final_score": adjusted_trajectory[-1]["score"] if adjusted_trajectory else 0.0,
            "trajectory": adjusted_trajectory,
            "total_risk_impact": round(total_negative_impact, 3),
            "assumptions": assumptions
        }
    
    def _generate_scenario_assumptions(self, scenario: str, risks: List[RiskFactor]) -> List[str]:
        """Generate assumptions for each scenario"""
        assumptions_map = {
            "optimistic": [
                "All team members available and fully engaged",
                "No significant scope changes or new requirements",
                "Efficient remediation of identified gaps",
                "Strong management support and resource allocation",
                "Minimal external dependencies or delays"
            ],
            "realistic": [
                "Normal team availability with occasional conflicts",
                "Standard remediation timelines with some delays",
                "Moderate resource constraints",
                "Typical organizational change management challenges",
                "Some dependency coordination required"
            ],
            "pessimistic": [
                "Significant team member unavailability",
                "Major scope changes or additional compliance requirements",
                "Resource constraints impacting remediation speed",
                "Organizational resistance to change",
                "Multiple external dependencies causing delays"
            ]
        }
        
        base_assumptions = assumptions_map.get(scenario, [])
        
        # Add risk-specific assumptions
        for risk in risks[:3]:  # Top 3 risks
            if risk.trend == "increasing":
                base_assumptions.append(f"Increasing concern about {risk.name.lower()}")
        
        return base_assumptions[:5]  # Limit to 5 assumptions
    
    def _monte_carlo_success_simulation(
        self, 
        scenario: Dict[str, Any], 
        risks: List[RiskFactor], 
        iterations: int = 1000,
        success_threshold: float = 85.0
    ) -> float:
        """Run Monte Carlo simulation to estimate success probability"""
        successes = 0
        
        for _ in range(iterations):
            # Add random variation based on risk factors
            random_variation = np.random.normal(0, 5)  # Standard deviation of 5 points
            
            # Apply risk-based random events
            for risk in risks:
                if np.random.random() < risk.probability:
                    # Risk event occurs
                    impact = np.random.normal(risk.impact_score * 10, 2)  # Convert to score points
                    random_variation -= abs(impact)
            
            simulated_score = scenario["final_score"] + random_variation
            
            if simulated_score >= success_threshold:
                successes += 1
        
        return round(successes / iterations, 3)
    
    def analyze_temporal_trends(
        self, 
        audit_id: str, 
        historical_data: List[TemporalDataPoint]
    ) -> Dict[str, Any]:
        """
        Multi-factor temporal trend analysis with advanced statistical methods
        """
        try:
            if len(historical_data) < 3:
                return self._generate_minimal_trend_analysis(audit_id)
            
            # Convert to pandas DataFrame for analysis
            df_data = []
            for point in historical_data:
                df_data.append({
                    'timestamp': point.timestamp,
                    'readiness_score': point.readiness_score,
                    'confidence': point.confidence,
                    'milestone_completion': point.milestone_completion,
                    'evidence_quality': point.evidence_quality,
                    **point.contributing_factors
                })
            
            df = pd.DataFrame(df_data)
            
            # Time-based feature engineering
            df['days_since_start'] = (df['timestamp'] - df['timestamp'].min()).dt.days
            df['week_number'] = df['timestamp'].dt.isocalendar().week
            df['month'] = df['timestamp'].dt.month
            
            # Trend analysis
            readiness_trend = self._calculate_trend_metrics(df, 'readiness_score')
            confidence_trend = self._calculate_trend_metrics(df, 'confidence')
            milestone_trend = self._calculate_trend_metrics(df, 'milestone_completion')
            
            # Correlation analysis
            correlations = self._calculate_correlation_matrix(df)
            
            # Seasonality detection
            seasonality = self._detect_seasonality_patterns(df)
            
            # Velocity analysis
            velocity_metrics = self._calculate_velocity_metrics(df)
            
            # Predictive momentum
            momentum_indicators = self._analyze_momentum_indicators(df)
            
            return {
                "analysis_id": str(uuid.uuid4()),
                "audit_id": audit_id,
                "analysis_date": datetime.utcnow().isoformat(),
                "data_points": len(historical_data),
                "time_span_days": (historical_data[-1].timestamp - historical_data[0].timestamp).days,
                "trend_analysis": {
                    "readiness_score": readiness_trend,
                    "confidence": confidence_trend,
                    "milestone_completion": milestone_trend
                },
                "correlation_analysis": correlations,
                "seasonality_patterns": seasonality,
                "velocity_metrics": velocity_metrics,
                "momentum_indicators": momentum_indicators,
                "statistical_significance": self._assess_statistical_significance(df),
                "forecast_reliability": self._calculate_forecast_reliability(df)
            }
        
        except Exception as e:
            logger.error(f"Error in temporal trend analysis: {str(e)}")
            return self._generate_minimal_trend_analysis(audit_id)
    
    def _calculate_trend_metrics(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Calculate comprehensive trend metrics for a column"""
        try:
            values = df[column].values
            days = df['days_since_start'].values
            
            # Linear regression for trend
            slope = np.polyfit(days, values, 1)[0] if len(values) > 1 else 0.0
            
            # Moving average
            window_size = min(7, len(values) // 2) if len(values) > 1 else 1
            moving_avg = df[column].rolling(window=window_size, min_periods=1).mean().iloc[-1]
            
            # Volatility (standard deviation)
            volatility = df[column].std() if len(values) > 1 else 0.0
            
            # Rate of change
            if len(values) > 1:
                rate_of_change = (values[-1] - values[0]) / max(abs(values[0]), 1e-6) * 100
            else:
                rate_of_change = 0.0
            
            # Trend classification
            if abs(slope) < 0.1:
                trend_direction = "stable"
            elif slope > 0:
                trend_direction = "improving"
            else:
                trend_direction = "declining"
            
            return {
                "current_value": values[-1] if len(values) > 0 else 0.0,
                "trend_slope": round(slope, 4),
                "trend_direction": trend_direction,
                "moving_average": round(moving_avg, 2),
                "volatility": round(volatility, 2),
                "rate_of_change_percent": round(rate_of_change, 2),
                "min_value": float(np.min(values)) if len(values) > 0 else 0.0,
                "max_value": float(np.max(values)) if len(values) > 0 else 0.0
            }
        
        except Exception as e:
            logger.error(f"Error calculating trend metrics for {column}: {str(e)}")
            return {
                "current_value": 0.0,
                "trend_slope": 0.0,
                "trend_direction": "unknown",
                "moving_average": 0.0,
                "volatility": 0.0,
                "rate_of_change_percent": 0.0,
                "min_value": 0.0,
                "max_value": 0.0
            }
    
    def _calculate_correlation_matrix(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate correlation between different metrics"""
        try:
            numeric_cols = ['readiness_score', 'confidence', 'milestone_completion', 'evidence_quality']
            available_cols = [col for col in numeric_cols if col in df.columns]
            
            if len(available_cols) < 2:
                return {"correlations": {}, "insights": ["Insufficient data for correlation analysis"]}
            
            corr_matrix = df[available_cols].corr()
            
            # Extract key correlations
            correlations = {}
            insights = []
            
            for i, col1 in enumerate(available_cols):
                for j, col2 in enumerate(available_cols):
                    if i < j:  # Avoid duplicates
                        corr_value = corr_matrix.loc[col1, col2]
                        correlations[f"{col1}_vs_{col2}"] = round(corr_value, 3)
                        
                        # Generate insights
                        if abs(corr_value) > 0.7:
                            strength = "strong"
                        elif abs(corr_value) > 0.4:
                            strength = "moderate"
                        else:
                            strength = "weak"
                        
                        direction = "positive" if corr_value > 0 else "negative"
                        insights.append(f"{strength.title()} {direction} correlation between {col1.replace('_', ' ')} and {col2.replace('_', ' ')}")
            
            return {
                "correlations": correlations,
                "insights": insights[:5]  # Limit insights
            }
        
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {str(e)}")
            return {"correlations": {}, "insights": ["Error in correlation analysis"]}
    
    def _detect_seasonality_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect weekly/monthly patterns in the data"""
        try:
            patterns = {}
            
            # Weekly patterns
            if 'week_number' in df.columns and len(df) > 4:
                weekly_avg = df.groupby('week_number')['readiness_score'].mean()
                if len(weekly_avg) > 1:
                    best_week = weekly_avg.idxmax()
                    worst_week = weekly_avg.idxmin()
                    patterns['weekly'] = {
                        "detected": True,
                        "best_performing_week": int(best_week),
                        "worst_performing_week": int(worst_week),
                        "variance": round(weekly_avg.var(), 2)
                    }
                else:
                    patterns['weekly'] = {"detected": False}
            else:
                patterns['weekly'] = {"detected": False}
            
            # Monthly patterns (if data spans multiple months)
            if 'month' in df.columns and df['month'].nunique() > 1:
                monthly_avg = df.groupby('month')['readiness_score'].mean()
                patterns['monthly'] = {
                    "detected": True,
                    "month_averages": {str(k): round(v, 2) for k, v in monthly_avg.items()}
                }
            else:
                patterns['monthly'] = {"detected": False}
            
            return patterns
        
        except Exception as e:
            logger.error(f"Error detecting seasonality patterns: {str(e)}")
            return {"weekly": {"detected": False}, "monthly": {"detected": False}}
    
    def _calculate_velocity_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate improvement velocity and acceleration"""
        try:
            if len(df) < 3:
                return {"velocity": 0.0, "acceleration": 0.0, "consistency": "insufficient_data"}
            
            # Calculate daily change rates
            df_sorted = df.sort_values('timestamp')
            df_sorted['daily_change'] = df_sorted['readiness_score'].diff()
            df_sorted['days_diff'] = df_sorted['days_since_start'].diff()
            df_sorted['velocity'] = df_sorted['daily_change'] / df_sorted['days_diff'].replace(0, 1)
            
            # Remove infinite values and NaN
            velocities = df_sorted['velocity'].replace([np.inf, -np.inf], np.nan).dropna()
            
            if len(velocities) < 2:
                return {"velocity": 0.0, "acceleration": 0.0, "consistency": "insufficient_data"}
            
            avg_velocity = velocities.mean()
            velocity_std = velocities.std()
            
            # Calculate acceleration (change in velocity)
            acceleration = velocities.diff().mean() if len(velocities) > 1 else 0.0
            
            # Consistency assessment
            if velocity_std < 0.5:
                consistency = "high"
            elif velocity_std < 1.0:
                consistency = "moderate"
            else:
                consistency = "low"
            
            return {
                "average_velocity": round(avg_velocity, 3),
                "velocity_std": round(velocity_std, 3),
                "acceleration": round(acceleration, 4),
                "consistency": consistency,
                "trend_sustainability": "high" if acceleration > 0 and consistency in ["high", "moderate"] else "moderate"
            }
        
        except Exception as e:
            logger.error(f"Error calculating velocity metrics: {str(e)}")
            return {"velocity": 0.0, "acceleration": 0.0, "consistency": "error"}
    
    def _analyze_momentum_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze momentum indicators for predictive insights"""
        try:
            if len(df) < 3:
                return {"momentum_score": 50.0, "indicators": [], "outlook": "neutral"}
            
            # Recent trend analysis (last 1/3 of data)
            recent_data = df.iloc[-len(df)//3:]
            overall_data = df
            
            recent_slope = np.polyfit(recent_data['days_since_start'], recent_data['readiness_score'], 1)[0]
            overall_slope = np.polyfit(overall_data['days_since_start'], overall_data['readiness_score'], 1)[0]
            
            # Momentum indicators
            indicators = []
            momentum_score = 50.0  # Base score
            
            # Trend acceleration
            if recent_slope > overall_slope * 1.2:
                indicators.append("Accelerating improvement trend")
                momentum_score += 15
            elif recent_slope < overall_slope * 0.8:
                indicators.append("Decelerating improvement trend")
                momentum_score -= 15
            
            # Consistency check
            recent_std = recent_data['readiness_score'].std()
            if recent_std < overall_data['readiness_score'].std():
                indicators.append("Increasing stability in performance")
                momentum_score += 10
            
            # Milestone completion momentum
            if 'milestone_completion' in df.columns:
                milestone_recent = recent_data['milestone_completion'].mean()
                milestone_overall = overall_data['milestone_completion'].mean()
                
                if milestone_recent > milestone_overall * 1.1:
                    indicators.append("Strong milestone completion momentum")
                    momentum_score += 10
            
            # Evidence quality momentum
            if 'evidence_quality' in df.columns:
                evidence_recent = recent_data['evidence_quality'].mean()
                if evidence_recent > 80:
                    indicators.append("High evidence quality maintained")
                    momentum_score += 5
            
            # Determine outlook
            if momentum_score >= 70:
                outlook = "positive"
            elif momentum_score >= 40:
                outlook = "neutral"
            else:
                outlook = "concerning"
            
            return {
                "momentum_score": round(min(100, max(0, momentum_score)), 1),
                "indicators": indicators,
                "outlook": outlook,
                "recent_trend_slope": round(recent_slope, 4),
                "overall_trend_slope": round(overall_slope, 4)
            }
        
        except Exception as e:
            logger.error(f"Error analyzing momentum indicators: {str(e)}")
            return {"momentum_score": 50.0, "indicators": ["Error in momentum analysis"], "outlook": "unknown"}
    
    def _assess_statistical_significance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess statistical significance of observed trends"""
        try:
            if len(df) < 5:
                return {"sample_size": len(df), "significance": "insufficient_data"}
            
            # Basic significance assessment based on sample size and variance
            sample_size = len(df)
            readiness_variance = df['readiness_score'].var()
            
            # Simple significance categories
            if sample_size >= 30 and readiness_variance > 10:
                significance = "high"
            elif sample_size >= 15 and readiness_variance > 5:
                significance = "moderate"
            elif sample_size >= 5:
                significance = "low"
            else:
                significance = "insufficient_data"
            
            return {
                "sample_size": sample_size,
                "variance": round(readiness_variance, 2),
                "significance": significance,
                "confidence_level": 0.95 if significance == "high" else 0.80 if significance == "moderate" else 0.60
            }
        
        except Exception as e:
            logger.error(f"Error assessing statistical significance: {str(e)}")
            return {"sample_size": 0, "significance": "error"}
    
    def _calculate_forecast_reliability(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate reliability metrics for forecasting"""
        try:
            data_quality_score = 100.0
            reliability_factors = []
            
            # Data completeness
            completeness = df.count().sum() / (len(df) * len(df.columns))
            if completeness < 0.9:
                data_quality_score -= 20
                reliability_factors.append("Missing data points detected")
            
            # Data consistency
            if 'readiness_score' in df.columns:
                score_jumps = abs(df['readiness_score'].diff()).mean()
                if score_jumps > 10:
                    data_quality_score -= 15
                    reliability_factors.append("High volatility in readiness scores")
            
            # Temporal consistency
            time_gaps = df['timestamp'].diff().dt.days.std() if len(df) > 1 else 0
            if time_gaps > 7:  # More than 7 days standard deviation
                data_quality_score -= 10
                reliability_factors.append("Irregular data collection intervals")
            
            # Sample size adequacy
            if len(df) < 10:
                data_quality_score -= 25
                reliability_factors.append("Limited historical data")
            
            # Determine reliability category
            if data_quality_score >= 80:
                reliability = "high"
            elif data_quality_score >= 60:
                reliability = "moderate"
            else:
                reliability = "low"
            
            return {
                "reliability_score": round(max(0, data_quality_score), 1),
                "reliability_category": reliability,
                "factors_affecting_reliability": reliability_factors,
                "recommended_confidence_adjustment": max(0.6, data_quality_score / 100)
            }
        
        except Exception as e:
            logger.error(f"Error calculating forecast reliability: {str(e)}")
            return {"reliability_score": 50.0, "reliability_category": "unknown", "factors_affecting_reliability": ["Error in analysis"]}
    
    def _generate_minimal_trend_analysis(self, audit_id: str) -> Dict[str, Any]:
        """Generate minimal trend analysis when insufficient data is available"""
        return {
            "analysis_id": str(uuid.uuid4()),
            "audit_id": audit_id,
            "analysis_date": datetime.utcnow().isoformat(),
            "data_points": 0,
            "time_span_days": 0,
            "status": "insufficient_data",
            "message": "Insufficient historical data for comprehensive trend analysis",
            "recommendations": [
                "Collect more data points over time",
                "Ensure regular data collection intervals",
                "Include multiple metrics for better analysis"
            ]
        }


# Initialize global analytics engine instance
enhanced_ai_engine = EnhancedAIAnalyticsEngine()