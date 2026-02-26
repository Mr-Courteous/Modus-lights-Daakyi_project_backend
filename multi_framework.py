"""
Multi-Framework Support for DAAKYI CompaaS
Architecture for handling multiple compliance frameworks with crosswalk mapping
Phase 2 MVP Implementation
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import uuid
from datetime import datetime

class FrameworkType(Enum):
    NIST_CSF_20 = "nist_csf_20"
    ISO_27001_2022 = "iso_27001_2022" 
    SOC_2 = "soc_2"
    GDPR = "gdpr"

@dataclass
class FrameworkControl:
    """Universal control structure for all frameworks"""
    id: str
    title: str
    description: str
    category: str
    subcategory: Optional[str] = None
    function: Optional[str] = None  # For frameworks that have function-level grouping
    framework_type: FrameworkType = None
    implementation_guidance: Optional[str] = None
    references: Optional[List[str]] = None
    priority: str = "medium"  # low, medium, high, critical
    
@dataclass
class Framework:
    """Framework definition with metadata"""
    id: str
    name: str
    version: str
    description: str
    framework_type: FrameworkType
    structure: Dict[str, Any]  # Hierarchical structure (functions -> categories -> controls)
    total_controls: int
    created_at: datetime
    updated_at: datetime

@dataclass
class CrosswalkMapping:
    """Maps controls between different frameworks"""
    id: str
    source_framework: FrameworkType
    source_control_id: str
    target_framework: FrameworkType
    target_control_id: str
    mapping_type: str  # "direct", "partial", "related", "similar"
    confidence_score: float  # 0.0 to 1.0
    mapping_rationale: str
    created_by: str = "system"
    created_at: datetime = None
    
class MultiFrameworkEngine:
    """Core engine for managing multiple compliance frameworks"""
    
    def __init__(self):
        self.frameworks = {}
        self.crosswalk_mappings = []
        self.active_frameworks = set()
        self._load_frameworks()
        self._load_crosswalk_mappings()
    
    def _load_frameworks(self):
        """Load all supported frameworks"""
        # Load NIST CSF 2.0 (existing)
        nist_data = self._convert_nist_to_framework()
        self.frameworks[FrameworkType.NIST_CSF_20] = nist_data
        
        # Load new frameworks
        self.frameworks[FrameworkType.ISO_27001_2022] = self._load_iso_27001()
        self.frameworks[FrameworkType.SOC_2] = self._load_soc_2()
        self.frameworks[FrameworkType.GDPR] = self._load_gdpr()
    
    def _convert_nist_to_framework(self) -> Framework:
        """Convert existing NIST framework to new structure"""
        from nist_framework import NIST_FRAMEWORK_DATA
        
        controls = []
        total_controls = 0
        
        for func_id, func_data in NIST_FRAMEWORK_DATA.items():
            for cat_id, cat_data in func_data["categories"].items():
                for subcat_id, subcat_desc in cat_data["subcategories"].items():
                    control = FrameworkControl(
                        id=subcat_id,
                        title=subcat_desc[:100] + "..." if len(subcat_desc) > 100 else subcat_desc,
                        description=subcat_desc,
                        function=func_data["name"],
                        category=cat_data["name"],
                        framework_type=FrameworkType.NIST_CSF_20,
                        priority="high"
                    )
                    controls.append(control)
                    total_controls += 1
        
        return Framework(
            id="nist_csf_20",
            name="NIST Cybersecurity Framework 2.0",
            version="2.0",
            description="The updated NIST framework with 6 functions for comprehensive cybersecurity risk management",
            framework_type=FrameworkType.NIST_CSF_20,
            structure=NIST_FRAMEWORK_DATA,
            total_controls=total_controls,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def _load_iso_27001(self) -> Framework:
        """Load ISO/IEC 27001:2022 Annex A controls"""
        iso_structure = {
            "A.5": {
                "name": "Information Security Policies",
                "categories": {
                    "A.5.1": {
                        "name": "Management Direction for Information Security",
                        "controls": {
                            "A.5.1.1": "Information security policies",
                            "A.5.1.2": "Information security roles and responsibilities"
                        }
                    }
                }
            },
            "A.6": {
                "name": "Organization of Information Security", 
                "categories": {
                    "A.6.1": {
                        "name": "Internal Organization",
                        "controls": {
                            "A.6.1.1": "Information security roles and responsibilities",
                            "A.6.1.2": "Segregation of duties",
                            "A.6.1.3": "Contact with authorities",
                            "A.6.1.4": "Contact with special interest groups",
                            "A.6.1.5": "Information security in project management"
                        }
                    },
                    "A.6.2": {
                        "name": "Mobile Devices and Teleworking",
                        "controls": {
                            "A.6.2.1": "Mobile device policy",
                            "A.6.2.2": "Teleworking"
                        }
                    }
                }
            },
            "A.7": {
                "name": "Human Resource Security",
                "categories": {
                    "A.7.1": {
                        "name": "Prior to Employment",
                        "controls": {
                            "A.7.1.1": "Screening",
                            "A.7.1.2": "Terms and conditions of employment"
                        }
                    },
                    "A.7.2": {
                        "name": "During Employment", 
                        "controls": {
                            "A.7.2.1": "Management responsibilities",
                            "A.7.2.2": "Information security awareness, education and training",
                            "A.7.2.3": "Disciplinary process"
                        }
                    },
                    "A.7.3": {
                        "name": "Termination and Change of Employment",
                        "controls": {
                            "A.7.3.1": "Termination or change of employment responsibilities"
                        }
                    }
                }
            },
            "A.8": {
                "name": "Asset Management",
                "categories": {
                    "A.8.1": {
                        "name": "Responsibility for Assets",
                        "controls": {
                            "A.8.1.1": "Inventory of assets",
                            "A.8.1.2": "Ownership of assets",
                            "A.8.1.3": "Acceptable use of assets",
                            "A.8.1.4": "Return of assets"
                        }
                    },
                    "A.8.2": {
                        "name": "Information Classification",
                        "controls": {
                            "A.8.2.1": "Classification of information",
                            "A.8.2.2": "Labelling of information",
                            "A.8.2.3": "Handling of assets"
                        }
                    },
                    "A.8.3": {
                        "name": "Media Handling",
                        "controls": {
                            "A.8.3.1": "Management of removable media",
                            "A.8.3.2": "Disposal of media",
                            "A.8.3.3": "Physical media transfer"
                        }
                    }
                }
            },
            "A.9": {
                "name": "Access Control",
                "categories": {
                    "A.9.1": {
                        "name": "Business Requirements of Access Control",
                        "controls": {
                            "A.9.1.1": "Access control policy",
                            "A.9.1.2": "Access to networks and network services"
                        }
                    },
                    "A.9.2": {
                        "name": "User Access Management",
                        "controls": {
                            "A.9.2.1": "User registration and de-registration",
                            "A.9.2.2": "User access provisioning",
                            "A.9.2.3": "Management of privileged access rights",
                            "A.9.2.4": "Management of secret authentication information of users",
                            "A.9.2.5": "Review of user access rights",
                            "A.9.2.6": "Removal or adjustment of access rights"
                        }
                    },
                    "A.9.3": {
                        "name": "User Responsibilities",
                        "controls": {
                            "A.9.3.1": "Use of secret authentication information"
                        }
                    },
                    "A.9.4": {
                        "name": "System and Application Access Control",
                        "controls": {
                            "A.9.4.1": "Information access restriction",
                            "A.9.4.2": "Secure log-on procedures",
                            "A.9.4.3": "Password management system",
                            "A.9.4.4": "Use of privileged utility programs",
                            "A.9.4.5": "Access control to program source code"
                        }
                    }
                }
            }
            # Additional ISO controls would continue here...
        }
        
        # Generate controls from structure
        controls = []
        total_controls = 0
        
        for section_id, section_data in iso_structure.items():
            for cat_id, cat_data in section_data["categories"].items():
                for control_id, control_desc in cat_data["controls"].items():
                    control = FrameworkControl(
                        id=control_id,
                        title=control_desc,
                        description=f"ISO 27001:2022 {control_id}: {control_desc}",
                        function=section_data["name"],
                        category=cat_data["name"],
                        framework_type=FrameworkType.ISO_27001_2022,
                        priority="high"
                    )
                    controls.append(control)
                    total_controls += 1
        
        return Framework(
            id="iso_27001_2022",
            name="ISO/IEC 27001:2022",
            version="2022",
            description="International standard for information security management systems (ISMS)",
            framework_type=FrameworkType.ISO_27001_2022,
            structure=iso_structure,
            total_controls=total_controls,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def _load_soc_2(self) -> Framework:
        """Load SOC 2 Trust Services Criteria"""
        soc2_structure = {
            "Security": {
                "name": "Security (Common Criteria)",
                "description": "Foundational security controls required for all SOC 2 audits",
                "categories": {
                    "CC1": {
                        "name": "Control Environment",
                        "controls": {
                            "CC1.1": "The entity demonstrates a commitment to integrity and ethical values",
                            "CC1.2": "The board of directors demonstrates independence from management",
                            "CC1.3": "Management establishes structures, reporting lines, and appropriate authorities",
                            "CC1.4": "The entity demonstrates a commitment to attract, develop, and retain competent individuals"
                        }
                    },
                    "CC2": {
                        "name": "Communication and Information",
                        "controls": {
                            "CC2.1": "The entity obtains or generates and uses relevant, quality information",
                            "CC2.2": "The entity internally communicates information necessary to support functioning",
                            "CC2.3": "The entity communicates with external parties regarding matters affecting functioning"
                        }
                    },
                    "CC3": {
                        "name": "Risk Assessment", 
                        "controls": {
                            "CC3.1": "The entity specifies objectives with sufficient clarity",
                            "CC3.2": "The entity identifies and analyzes risks to the achievement of objectives",
                            "CC3.3": "The entity considers the potential for fraud in assessing risks",
                            "CC3.4": "The entity identifies and assesses changes that could significantly impact the system"
                        }
                    },
                    "CC4": {
                        "name": "Monitoring Activities",
                        "controls": {
                            "CC4.1": "The entity selects, develops, and performs ongoing and/or separate evaluations",
                            "CC4.2": "The entity evaluates and communicates internal control deficiencies"
                        }
                    },
                    "CC5": {
                        "name": "Control Activities",
                        "controls": {
                            "CC5.1": "The entity selects and develops control activities that contribute to the mitigation of risks",
                            "CC5.2": "The entity selects and develops general control activities over technology",
                            "CC5.3": "The entity deploys control activities through policies and procedures"
                        }
                    },
                    "CC6": {
                        "name": "Logical and Physical Access Controls",
                        "controls": {
                            "CC6.1": "The entity implements logical access security software and infrastructure",
                            "CC6.2": "The entity restricts logical access to data and system resources",
                            "CC6.3": "The entity manages access credentials to data and system resources",
                            "CC6.4": "The entity restricts physical access to data and system resources",
                            "CC6.5": "The entity discontinues logical and physical access"
                        }
                    },
                    "CC7": {
                        "name": "System Operations",
                        "controls": {
                            "CC7.1": "The entity uses detection and monitoring procedures to identify security incidents",
                            "CC7.2": "The entity responds to identified security incidents",
                            "CC7.3": "The entity evaluates security events to determine whether they impair system availability",
                            "CC7.4": "The entity responds to system availability issues"
                        }
                    },
                    "CC8": {
                        "name": "Change Management",
                        "controls": {
                            "CC8.1": "The entity authorizes, designs, develops or acquires, tests, and implements changes to infrastructure, data, software, and procedures"
                        }
                    },
                    "CC9": {
                        "name": "Risk Mitigation",
                        "controls": {
                            "CC9.1": "The entity identifies, selects, and develops risk mitigation activities for risks arising from potential business disruptions",
                            "CC9.2": "The entity assesses and manages risks associated with vendors and business partners"
                        }
                    }
                }
            },
            "Availability": {
                "name": "Availability",
                "description": "System availability as committed or agreed upon",
                "categories": {
                    "A1": {
                        "name": "Availability Controls",
                        "controls": {
                            "A1.1": "The entity maintains, monitors, and evaluates current processing capacity",
                            "A1.2": "The entity authorizes and manages access to minimize availability risks",
                            "A1.3": "The entity maintains availability and recovery plans and procedures"
                        }
                    }
                }
            },
            "Processing_Integrity": {
                "name": "Processing Integrity",
                "description": "System processing is complete, valid, accurate, timely, and authorized",
                "categories": {
                    "PI1": {
                        "name": "Processing Integrity Controls",
                        "controls": {
                            "PI1.1": "The entity obtains or generates, uses, and communicates relevant, quality information regarding the objectives related to processing",
                            "PI1.2": "The entity implements controls over system inputs, processing, and outputs"
                        }
                    }
                }
            },
            "Confidentiality": {
                "name": "Confidentiality", 
                "description": "Information designated as confidential is protected as committed or agreed upon",
                "categories": {
                    "C1": {
                        "name": "Confidentiality Controls",
                        "controls": {
                            "C1.1": "The entity identifies and maintains confidential information",
                            "C1.2": "The entity disposes of confidential information to meet the entity's objectives"
                        }
                    }
                }
            },
            "Privacy": {
                "name": "Privacy",
                "description": "Personal information is collected, used, retained, disclosed, and disposed of in conformity with commitments in the entity's privacy notice",
                "categories": {
                    "P1": {
                        "name": "Privacy Controls",
                        "controls": {
                            "P1.1": "The entity provides notice to data subjects about its privacy practices",
                            "P1.2": "The entity communicates choices available regarding the collection, use, retention, disclosure, and disposal of personal information",
                            "P1.3": "The entity collects personal information consistent with the entity's privacy notice",
                            "P1.4": "The entity uses personal information consistent with the entity's privacy notice",
                            "P1.5": "The entity retains personal information consistent with the entity's privacy notice",
                            "P1.6": "The entity discloses personal information to third parties consistent with the entity's privacy notice",
                            "P1.7": "The entity disposes of personal information consistent with the entity's privacy notice",
                            "P1.8": "The entity provides data subjects with access to their personal information for review and update"
                        }
                    }
                }
            }
        }
        
        # Generate controls from structure
        controls = []
        total_controls = 0
        
        for func_id, func_data in soc2_structure.items():
            for cat_id, cat_data in func_data["categories"].items():
                for control_id, control_desc in cat_data["controls"].items():
                    control = FrameworkControl(
                        id=control_id,
                        title=control_desc[:80] + "..." if len(control_desc) > 80 else control_desc,
                        description=control_desc,
                        function=func_data["name"],
                        category=cat_data["name"],
                        framework_type=FrameworkType.SOC_2,
                        priority="high"
                    )
                    controls.append(control)
                    total_controls += 1
        
        return Framework(
            id="soc_2",
            name="SOC 2 Trust Services Criteria",
            version="2019",
            description="AICPA Trust Services Criteria for Security, Availability, Processing Integrity, Confidentiality, and Privacy",
            framework_type=FrameworkType.SOC_2,
            structure=soc2_structure,
            total_controls=total_controls,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def _load_gdpr(self) -> Framework:
        """Load GDPR compliance requirements"""
        gdpr_structure = {
            "Principles": {
                "name": "Data Protection Principles (Article 5)",
                "categories": {
                    "Art5": {
                        "name": "Principles relating to processing of personal data",
                        "controls": {
                            "GDPR-5.1.a": "Personal data shall be processed lawfully, fairly and transparently",
                            "GDPR-5.1.b": "Personal data shall be collected for specified, explicit and legitimate purposes",
                            "GDPR-5.1.c": "Personal data shall be adequate, relevant and limited to what is necessary",
                            "GDPR-5.1.d": "Personal data shall be accurate and kept up to date",
                            "GDPR-5.1.e": "Personal data shall be kept in a form which permits identification for no longer than necessary",
                            "GDPR-5.1.f": "Personal data shall be processed in a manner that ensures appropriate security"
                        }
                    }
                }
            },
            "Security": {
                "name": "Security of Processing (Article 32)",
                "categories": {
                    "Art32": {
                        "name": "Security of processing",
                        "controls": {
                            "GDPR-32.1.a": "The pseudonymisation and encryption of personal data",
                            "GDPR-32.1.b": "The ability to ensure the ongoing confidentiality, integrity, availability and resilience of processing systems",
                            "GDPR-32.1.c": "The ability to restore the availability and access to personal data in a timely manner in the event of incident",
                            "GDPR-32.1.d": "A process for regularly testing, assessing and evaluating the effectiveness of technical and organisational measures",
                            "GDPR-32.2": "In assessing the appropriate level of security account shall be taken of the risks that are presented by processing"
                        }
                    }
                }
            },
            "Breach_Notification": {
                "name": "Personal Data Breach Notification (Article 33)",
                "categories": {
                    "Art33": {
                        "name": "Notification of a personal data breach to the supervisory authority",
                        "controls": {
                            "GDPR-33.1": "Personal data breach shall be notified to supervisory authority within 72 hours",
                            "GDPR-33.2": "The notification shall not be required if personal data breach is unlikely to result in a risk to rights and freedoms",
                            "GDPR-33.3": "Notification shall describe the nature of the personal data breach including categories and approximate number of data subjects concerned",
                            "GDPR-33.4": "The notification shall communicate the name and contact details of the data protection officer",
                            "GDPR-33.5": "The notification shall describe the likely consequences of the personal data breach"
                        }
                    }
                }
            },
            "Impact_Assessment": {
                "name": "Data Protection Impact Assessment (Article 35)",
                "categories": {
                    "Art35": {
                        "name": "Data protection impact assessment",
                        "controls": {
                            "GDPR-35.1": "Where processing is likely to result in a high risk to rights and freedoms, controller shall carry out a DPIA",
                            "GDPR-35.2": "A DPIA shall in particular be required for systematic and extensive evaluation of personal aspects",
                            "GDPR-35.3": "A DPIA shall in particular be required for processing on a large scale of special categories of data",
                            "GDPR-35.4": "A DPIA shall in particular be required for systematic monitoring of publicly accessible area on a large scale",
                            "GDPR-35.7": "The assessment shall contain a systematic description of the envisaged processing operations and purposes",
                            "GDPR-35.8": "The assessment shall contain an assessment of the risks to the rights and freedoms of data subjects",
                            "GDPR-35.9": "The assessment shall contain measures envisaged to address the risks and demonstrate compliance"
                        }
                    }
                }
            },
            "Rights": {
                "name": "Data Subject Rights",
                "categories": {
                    "DataSubjectRights": {
                        "name": "Individual Rights under GDPR",
                        "controls": {
                            "GDPR-15": "Right of access by the data subject",
                            "GDPR-16": "Right to rectification", 
                            "GDPR-17": "Right to erasure ('right to be forgotten')",
                            "GDPR-18": "Right to restriction of processing",
                            "GDPR-20": "Right to data portability",
                            "GDPR-21": "Right to object",
                            "GDPR-22": "Automated individual decision-making, including profiling"
                        }
                    }
                }
            }
        }
        
        # Generate controls from structure
        controls = []
        total_controls = 0
        
        for section_id, section_data in gdpr_structure.items():
            for cat_id, cat_data in section_data["categories"].items():
                for control_id, control_desc in cat_data["controls"].items():
                    control = FrameworkControl(
                        id=control_id,
                        title=control_desc[:80] + "..." if len(control_desc) > 80 else control_desc,
                        description=control_desc,
                        function=section_data["name"],
                        category=cat_data["name"],
                        framework_type=FrameworkType.GDPR,
                        priority="critical" if "breach" in control_desc.lower() or "notification" in control_desc.lower() else "high"
                    )
                    controls.append(control)
                    total_controls += 1
        
        return Framework(
            id="gdpr",
            name="General Data Protection Regulation (GDPR)",
            version="2018",
            description="EU regulation on data protection and privacy in the European Union and the European Economic Area",
            framework_type=FrameworkType.GDPR,
            structure=gdpr_structure,
            total_controls=total_controls,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def _load_crosswalk_mappings(self):
        """Initialize crosswalk mappings between frameworks"""
        # Sample crosswalk mappings - these would be expanded with comprehensive mappings
        sample_mappings = [
            # NIST to ISO 27001 mappings
            CrosswalkMapping(
                id=str(uuid.uuid4()),
                source_framework=FrameworkType.NIST_CSF_20,
                source_control_id="GV.OC-01",
                target_framework=FrameworkType.ISO_27001_2022,
                target_control_id="A.5.1.1",
                mapping_type="related",
                confidence_score=0.85,
                mapping_rationale="Both controls address organizational context and information security policies",
                created_at=datetime.now()
            ),
            # NIST to SOC 2 mappings
            CrosswalkMapping(
                id=str(uuid.uuid4()),
                source_framework=FrameworkType.NIST_CSF_20,
                source_control_id="GV.RM-01",
                target_framework=FrameworkType.SOC_2,
                target_control_id="CC3.1",
                mapping_type="partial",
                confidence_score=0.78,
                mapping_rationale="Risk management strategy relates to specifying objectives with clarity",
                created_at=datetime.now()
            ),
            # NIST to GDPR mappings
            CrosswalkMapping(
                id=str(uuid.uuid4()),
                source_framework=FrameworkType.NIST_CSF_20,
                source_control_id="PR.DS-01",  # Data-at-rest protection
                target_framework=FrameworkType.GDPR,
                target_control_id="GDPR-32.1.a",
                mapping_type="direct",
                confidence_score=0.92,
                mapping_rationale="Both controls address encryption and pseudonymisation of personal data",
                created_at=datetime.now()
            )
        ]
        
        self.crosswalk_mappings.extend(sample_mappings)
    
    def get_available_frameworks(self) -> List[Dict[str, Any]]:
        """Get list of all available frameworks"""
        return [
            {
                "id": framework.id,
                "name": framework.name,
                "version": framework.version,
                "description": framework.description,
                "framework_type": framework.framework_type.value,
                "total_controls": framework.total_controls,
                "is_active": framework.framework_type in self.active_frameworks
            }
            for framework in self.frameworks.values()
        ]
    
    def activate_framework(self, framework_type: FrameworkType) -> bool:
        """Activate a framework for use in assessments"""
        if framework_type in self.frameworks:
            self.active_frameworks.add(framework_type)
            return True
        return False
    
    def deactivate_framework(self, framework_type: FrameworkType) -> bool:
        """Deactivate a framework"""
        if framework_type in self.active_frameworks:
            self.active_frameworks.remove(framework_type)
            return True
        return False
    
    def get_framework_controls(self, framework_type: FrameworkType) -> List[FrameworkControl]:
        """Get all controls for a specific framework"""
        if framework_type not in self.frameworks:
            return []
        
        framework = self.frameworks[framework_type]
        controls = []
        
        # Parse controls from framework structure
        for section_id, section_data in framework.structure.items():
            if "categories" in section_data:
                for cat_id, cat_data in section_data["categories"].items():
                    control_key = "controls" if "controls" in cat_data else "subcategories"
                    if control_key in cat_data:
                        for control_id, control_desc in cat_data[control_key].items():
                            control = FrameworkControl(
                                id=control_id,
                                title=control_desc[:80] + "..." if len(control_desc) > 80 else control_desc,
                                description=control_desc,
                                function=section_data["name"],
                                category=cat_data["name"],
                                framework_type=framework_type
                            )
                            controls.append(control)
        
        return controls
    
    def get_crosswalk_mappings(self, source_framework: FrameworkType, target_framework: FrameworkType) -> List[CrosswalkMapping]:
        """Get crosswalk mappings between two frameworks"""
        return [
            mapping for mapping in self.crosswalk_mappings
            if mapping.source_framework == source_framework and mapping.target_framework == target_framework
        ]
    
    def find_related_controls(self, control_id: str, source_framework: FrameworkType) -> List[Tuple[FrameworkControl, CrosswalkMapping]]:
        """Find related controls across all active frameworks"""
        related_controls = []
        
        for mapping in self.crosswalk_mappings:
            if mapping.source_control_id == control_id and mapping.source_framework == source_framework:
                target_controls = self.get_framework_controls(mapping.target_framework)
                target_control = next((c for c in target_controls if c.id == mapping.target_control_id), None)
                if target_control:
                    related_controls.append((target_control, mapping))
        
        return related_controls
    
    def create_multi_framework_assessment(self, organization_id: str, selected_frameworks: List[FrameworkType]) -> Dict[str, Any]:
        """Create an assessment covering multiple frameworks"""
        assessment_id = str(uuid.uuid4())
        
        # Collect all controls from selected frameworks
        all_controls = []
        for framework_type in selected_frameworks:
            if framework_type in self.active_frameworks:
                controls = self.get_framework_controls(framework_type)
                all_controls.extend(controls)
        
        # Generate crosswalk analysis
        crosswalk_analysis = {}
        for i, framework1 in enumerate(selected_frameworks):
            for framework2 in selected_frameworks[i+1:]:
                key = f"{framework1.value}_to_{framework2.value}"
                mappings = self.get_crosswalk_mappings(framework1, framework2)
                crosswalk_analysis[key] = {
                    "total_mappings": len(mappings),
                    "direct_mappings": len([m for m in mappings if m.mapping_type == "direct"]),
                    "coverage_percentage": len(mappings) / max(len(self.get_framework_controls(framework1)), 1) * 100
                }
        
        return {
            "assessment_id": assessment_id,
            "organization_id": organization_id,
            "frameworks": [f.value for f in selected_frameworks],
            "total_controls": len(all_controls),
            "controls_by_framework": {
                f.value: len(self.get_framework_controls(f)) for f in selected_frameworks
            },
            "crosswalk_analysis": crosswalk_analysis,
            "created_at": datetime.now().isoformat()
        }

# Global instance
multi_framework_engine = MultiFrameworkEngine()

def get_multi_framework_engine() -> MultiFrameworkEngine:
    """Get the global multi-framework engine instance"""
    return multi_framework_engine