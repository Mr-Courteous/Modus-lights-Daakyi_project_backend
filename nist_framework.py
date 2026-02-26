"""
NIST CSF 2.0 Framework Implementation
Complete taxonomy and control definitions for DAAKYI CompaaS
"""

from typing import Dict, List, Any, Optional
from models import NISTFunction, NISTCategory, NISTSubcategory

# NIST CSF 2.0 Complete Framework Data
NIST_FRAMEWORK_DATA = {
    "GV": {
        "name": "Govern",
        "description": "The organization's cybersecurity risk management strategy, expectations, and policy are established, communicated, and monitored.",
        "categories": {
            "GV.OC": {
                "name": "Organizational Context",
                "subcategories": {
                    "GV.OC-01": "The organizational mission is understood and informs cybersecurity risk management",
                    "GV.OC-02": "Internal and external stakeholders are understood, and their needs and expectations regarding cybersecurity risk management are understood",
                    "GV.OC-03": "Legal, regulatory, and contractual requirements regarding cybersecurity are understood and managed",
                    "GV.OC-04": "Critical objectives, functions, and services are understood and prioritized",
                    "GV.OC-05": "Outcomes, roles, and responsibilities for cybersecurity risk management are established and communicated"
                }
            },
            "GV.RM": {
                "name": "Risk Management Strategy", 
                "subcategories": {
                    "GV.RM-01": "A risk management strategy is established and is informed by organizational context",
                    "GV.RM-02": "Risk appetite and risk tolerance statements are established, communicated, and maintained",
                    "GV.RM-03": "Cybersecurity risk management activities and outcomes are included in enterprise risk management processes",
                    "GV.RM-04": "Strategic direction for cybersecurity risk management is informed by risk management strategy outcomes",
                    "GV.RM-05": "Risk management strategy is informed by and influences the organizational risk appetite and risk tolerance statements",
                    "GV.RM-06": "Risk management strategy is informed by and influences strategic cybersecurity planning and investment",
                    "GV.RM-07": "Risk management strategy is informed by and influences cybersecurity policy and procedures"
                }
            },
            "GV.RR": {
                "name": "Risk Reporting",
                "subcategories": {
                    "GV.RR-01": "Risk reporting processes and procedures are established",
                    "GV.RR-02": "Risk information is aggregated and communicated to stakeholders",
                    "GV.RR-03": "Risk reporting is reviewed to inform policy and strategic decision-making",
                    "GV.RR-04": "Senior management and executive leadership communicate cybersecurity risk information to stakeholders"
                }
            },
            "GV.SC": {
                "name": "Supply Chain Risk Management",
                "subcategories": {
                    "GV.SC-01": "A supply chain risk management strategy is established and agreed upon by organizational stakeholders",
                    "GV.SC-02": "Supply chain risk management objectives are supported by the organizational cybersecurity strategy",
                    "GV.SC-03": "Supply chain risk management is integrated with other organizational risk management processes",
                    "GV.SC-04": "Suppliers are known and prioritized by criticality",
                    "GV.SC-05": "Requirements to address cybersecurity risks in supply chains are established, prioritized, and integrated into contracts and other types of agreements with suppliers and other relevant third parties",
                    "GV.SC-06": "Planning and due diligence are performed to reduce risks before entering into formal supplier or other third-party relationships",
                    "GV.SC-07": "The risks posed by suppliers, their products, and their services are understood, recorded, prioritized, assessed, responded to, and monitored over the course of the relationship",
                    "GV.SC-08": "Relevant supply chain risk information is identified, established, assessed, managed, and agreed to by organizational stakeholders",
                    "GV.SC-09": "Supply chain risk information is shared with suppliers and relevant stakeholders",
                    "GV.SC-10": "Cybersecurity requirements are included in acquisition and procurement processes"
                }
            }
        }
    },
    "ID": {
        "name": "Identify", 
        "description": "The organization's current cybersecurity risks are understood.",
        "categories": {
            "ID.AM": {
                "name": "Asset Management",
                "subcategories": {
                    "ID.AM-01": "Inventories of hardware managed by the organization are maintained",
                    "ID.AM-02": "Inventories of software, services, and systems managed by the organization are maintained", 
                    "ID.AM-03": "Representations of the organization's authorized network communications and internal network flows are maintained",
                    "ID.AM-04": "Inventories of services provided by suppliers are maintained",
                    "ID.AM-05": "Assets are prioritized based on classification, criticality, resources, and business functions",
                    "ID.AM-06": "Cybersecurity roles, responsibilities, and authorities are established for the organization's workforce",
                    "ID.AM-07": "Inventories of data and corresponding metadata for those data are maintained",
                    "ID.AM-08": "Systems, hardware, software, services, and data are managed throughout their life cycles"
                }
            },
            "ID.RA": {
                "name": "Risk Assessment",
                "subcategories": {
                    "ID.RA-01": "Vulnerabilities in assets are identified, validated, and recorded",
                    "ID.RA-02": "Cyber threat intelligence is gathered and analyzed to understand cyber threats",
                    "ID.RA-03": "Internal and external threat sources are identified and characterized",
                    "ID.RA-04": "Potential impacts and likelihood of cyber threats to the organization are identified and recorded",
                    "ID.RA-05": "Threats, vulnerabilities, likelihood, and impacts are used to understand inherent risk and inform risk response prioritization",
                    "ID.RA-06": "Risk responses are chosen, prioritized, planned, tracked, and communicated",
                    "ID.RA-07": "Changes and exceptions are managed, assessed for risk impact, recorded, and tracked",
                    "ID.RA-08": "Processes for receiving, analyzing, and responding to vulnerability disclosures are established",
                    "ID.RA-09": "The authenticity and integrity of hardware and software are assessed prior to acquisition and use",
                    "ID.RA-10": "Critical suppliers are assessed prior to acquisition and periodically thereafter"
                }
            },
            "ID.IM": {
                "name": "Improvement",
                "subcategories": {
                    "ID.IM-01": "Improvements to organizational cybersecurity risk management are identified from evaluations",
                    "ID.IM-02": "Improvement opportunities are identified from security tests, exercises, lessons learned, and reviews",
                    "ID.IM-03": "Improvements are made to organizational processes, procedures, and capabilities",
                    "ID.IM-04": "Incident response plans and other cybersecurity plans that affect operations are established, communicated, maintained, and improved"
                }
            }
        }
    },
    "PR": {
        "name": "Protect",
        "description": "Safeguards to ensure delivery of critical infrastructure services are implemented.",
        "categories": {
            "PR.AA": {
                "name": "Identity Management, Authentication and Access Control",
                "subcategories": {
                    "PR.AA-01": "Identities and credentials for authorized individuals, services, and hardware are issued, managed, verified, revoked, and audited",
                    "PR.AA-02": "Identities are proofed and bound to credentials based on organizational requirements", 
                    "PR.AA-03": "Identity lifecycle management is performed",
                    "PR.AA-04": "Credential lifecycle management is performed",
                    "PR.AA-05": "Access permissions, entitlements, and authorizations are defined, approved, granted, managed, and revoked",
                    "PR.AA-06": "Physical and logical access to assets is managed based on business functions, roles, and the principle of least privilege"
                }
            },
            "PR.AT": {
                "name": "Awareness and Training",
                "subcategories": {
                    "PR.AT-01": "Personnel are trained and made aware of their cybersecurity responsibilities and how to perform them",
                    "PR.AT-02": "Individuals in cybersecurity roles are trained to perform their responsibilities"
                }
            },
            "PR.DS": {
                "name": "Data Security",
                "subcategories": {
                    "PR.DS-01": "The confidentiality, integrity, and availability of data-at-rest are protected",
                    "PR.DS-02": "The confidentiality, integrity, and availability of data-in-transit are protected", 
                    "PR.DS-03": "Systems and assets are formally managed throughout removal, transfers, and disposition",
                    "PR.DS-04": "Adequate capacity to ensure availability is maintained",
                    "PR.DS-05": "Protections against data leaks and spills are implemented",
                    "PR.DS-06": "Integrity checking mechanisms are used to verify software, firmware, and information integrity",
                    "PR.DS-07": "The development and testing environment(s) are managed separately from operational environments",
                    "PR.DS-08": "Integrity checking mechanisms are used to verify hardware integrity",
                    "PR.DS-09": "Managing data throughout its lifecycle is based on the organization's risk strategy to protect the confidentiality, integrity, and availability of information",
                    "PR.DS-10": "The confidentiality, integrity, and availability of data processing is protected",
                    "PR.DS-11": "Backups of information are conducted, maintained, and tested"
                }
            },
            "PR.IP": {
                "name": "Information Protection Processes and Procedures",
                "subcategories": {
                    "PR.IP-01": "Baseline configurations that reflect approved settings and security requirements are developed and maintained",
                    "PR.IP-02": "Systems development life cycle processes include cybersecurity considerations",
                    "PR.IP-03": "Configuration change control processes are in place",
                    "PR.IP-04": "Backups of information are conducted, maintained, and tested",
                    "PR.IP-05": "Policy and procedures are in place for secure disposal or reuse of equipment",
                    "PR.IP-06": "Data is destroyed according to a documented policy",
                    "PR.IP-07": "Protection processes are continuously improved",
                    "PR.IP-08": "The effectiveness of protection technologies is shared with appropriate parties",
                    "PR.IP-09": "Response and recovery plans are in place and managed",
                    "PR.IP-10": "Testing of response and recovery plans is conducted",
                    "PR.IP-11": "Cybersecurity is included in human resources practices",
                    "PR.IP-12": "A vulnerability management plan is developed and implemented"
                }
            },
            "PR.MA": {
                "name": "Maintenance",
                "subcategories": {
                    "PR.MA-01": "Maintenance and repair of organizational assets are performed and logged, with approved and controlled tools",
                    "PR.MA-02": "Remote maintenance of organizational assets is approved, logged, and performed in a manner that prevents unauthorized access"
                }
            },
            "PR.PT": {
                "name": "Protective Technology",
                "subcategories": {
                    "PR.PT-01": "Audit/log records are determined, documented, implemented, and reviewed in accordance with policy",
                    "PR.PT-02": "Removable media is protected and its use restricted according to policy",
                    "PR.PT-03": "The principle of least functionality is incorporated by configuring systems to provide only essential capabilities",
                    "PR.PT-04": "Communications and control networks are protected",
                    "PR.PT-05": "Mechanisms are implemented to achieve resilience requirements in normal and adverse situations"
                }
            }
        }
    },
    "DE": {
        "name": "Detect",
        "description": "Activities to identify the occurrence of a cybersecurity event are developed and implemented.",
        "categories": {
            "DE.AE": {
                "name": "Anomalies and Events",
                "subcategories": {
                    "DE.AE-01": "Networks and network services are monitored to find potentially malicious activity",
                    "DE.AE-02": "Authorized and unauthorized software is monitored to find potentially malicious activity",
                    "DE.AE-03": "Personnel activity and technology usage are monitored to find potentially malicious activity",
                    "DE.AE-04": "Malicious code is detected",
                    "DE.AE-05": "Unauthorized mobile code is detected",
                    "DE.AE-06": "External service provider activity is monitored to detect potential cybersecurity events",
                    "DE.AE-07": "Monitoring is performed using local and remote access logging",
                    "DE.AE-08": "Detected events are analyzed to understand attack targets and methods"
                }
            },
            "DE.CM": {
                "name": "Security Continuous Monitoring",
                "subcategories": {
                    "DE.CM-01": "Networks and network services are monitored",
                    "DE.CM-02": "The physical environment is monitored",
                    "DE.CM-03": "Personnel activity is monitored",
                    "DE.CM-04": "Malicious code is detected in authorized and unauthorized software",
                    "DE.CM-05": "Unauthorized mobile code is detected",
                    "DE.CM-06": "External service provider activities are monitored",
                    "DE.CM-07": "Monitoring for unauthorized personnel, connections, devices, and software is performed",
                    "DE.CM-08": "Vulnerability scans are performed",
                    "DE.CM-09": "Computing resources are monitored"
                }
            }
        }
    },
    "RS": {
        "name": "Respond",
        "description": "Activities to respond to a detected cybersecurity incident are developed and implemented.",
        "categories": {
            "RS.RP": {
                "name": "Response Planning",
                "subcategories": {
                    "RS.RP-01": "A response plan that addresses roles, responsibilities, and activities is developed, maintained, and executed",
                    "RS.RP-02": "Response and recovery plans are updated",
                    "RS.RP-03": "Response processes and procedures are executed during and after an incident",
                    "RS.RP-04": "The organization coordinates response and recovery activities with internal and external stakeholders",
                    "RS.RP-05": "The response plan is updated based on lessons learned and reviews"
                }
            },
            "RS.CO": {
                "name": "Communications",
                "subcategories": {
                    "RS.CO-01": "Personnel are aware of their roles and order of operations when a response is needed",
                    "RS.CO-02": "Internal and external stakeholders are notified of cybersecurity incidents",
                    "RS.CO-03": "Information is shared consistent with response plans",
                    "RS.CO-04": "Coordination with stakeholders occurs consistent with response plans",
                    "RS.CO-05": "Voluntary information sharing occurs with external stakeholders to achieve broader cybersecurity situational awareness"
                }
            },
            "RS.AN": {
                "name": "Analysis",
                "subcategories": {
                    "RS.AN-01": "Indicators associated with cybersecurity incidents are identified, collected, examined, and analyzed",
                    "RS.AN-02": "The full scope and impact of cybersecurity incidents are understood",
                    "RS.AN-03": "Forensics are performed",
                    "RS.AN-04": "Incidents are categorized consistent with response plans",
                    "RS.AN-05": "Processes are established to receive, analyze, and respond to vulnerability disclosures",
                    "RS.AN-06": "Actions performed during an investigation are recorded",
                    "RS.AN-07": "The knowledge gained from research and development is applied to response activities",
                    "RS.AN-08": "Incidents are resolved"
                }
            },
            "RS.MI": {
                "name": "Mitigation",
                "subcategories": {
                    "RS.MI-01": "Incidents are contained",
                    "RS.MI-02": "Incidents are mitigated",
                    "RS.MI-03": "Newly identified vulnerabilities are mitigated or documented as accepted risks"
                }
            },
            "RS.IM": {
                "name": "Improvements",
                "subcategories": {
                    "RS.IM-01": "Response plans incorporate lessons learned",
                    "RS.IM-02": "Response strategies are updated"
                }
            }
        }
    },
    "RC": {
        "name": "Recover",
        "description": "Activities to restore services or capabilities that were impaired due to a cybersecurity incident are developed and implemented.",
        "categories": {
            "RC.RP": {
                "name": "Recovery Planning",
                "subcategories": {
                    "RC.RP-01": "A recovery plan that addresses roles, responsibilities, and activities is developed, maintained, and executed",
                    "RC.RP-02": "Recovery strategies are updated",
                    "RC.RP-03": "The recovery plan is updated based on lessons learned and reviews",
                    "RC.RP-04": "Recovery time and point objectives are updated",
                    "RC.RP-05": "Legal hold and data breach notification processes are established"
                }
            },
            "RC.IM": {
                "name": "Improvements",
                "subcategories": {
                    "RC.IM-01": "Recovery plans incorporate lessons learned",
                    "RC.IM-02": "Recovery strategies are updated"
                }
            },
            "RC.CO": {
                "name": "Communications",
                "subcategories": {
                    "RC.CO-01": "Public relations are managed",
                    "RC.CO-02": "Reputation is repaired after an incident",
                    "RC.CO-03": "Communication with stakeholders is coordinated",
                    "RC.CO-04": "Recovery activities are communicated to organizational stakeholders, cybersecurity vendors, and law enforcement"
                }
            }
        }
    }
}

class NISTFrameworkService:
    """Service for managing NIST CSF 2.0 framework data and operations"""
    
    def __init__(self):
        self.framework_data = NIST_FRAMEWORK_DATA
    
    def get_all_functions(self) -> List[Dict[str, Any]]:
        """Get all NIST CSF 2.0 functions"""
        functions = []
        for func_id, func_data in self.framework_data.items():
            functions.append({
                "id": func_id,
                "name": func_data["name"],
                "description": func_data["description"],
                "category_count": len(func_data["categories"])
            })
        return functions
    
    def get_function_details(self, function_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific function"""
        if function_id not in self.framework_data:
            return None
            
        func_data = self.framework_data[function_id]
        categories = []
        
        for cat_id, cat_data in func_data["categories"].items():
            subcategories = []
            for subcat_id, subcat_desc in cat_data["subcategories"].items():
                subcategories.append({
                    "id": subcat_id,
                    "description": subcat_desc
                })
            
            categories.append({
                "id": cat_id,
                "name": cat_data["name"],
                "subcategories": subcategories
            })
        
        return {
            "id": function_id,
            "name": func_data["name"],
            "description": func_data["description"],
            "categories": categories
        }
    
    def get_all_controls(self) -> List[Dict[str, Any]]:
        """Get all NIST CSF 2.0 subcategories (controls)"""
        controls = []
        
        for func_id, func_data in self.framework_data.items():
            for cat_id, cat_data in func_data["categories"].items():
                for subcat_id, subcat_desc in cat_data["subcategories"].items():
                    controls.append({
                        "id": subcat_id,
                        "description": subcat_desc,
                        "function_id": func_id,
                        "function_name": func_data["name"],
                        "category_id": cat_id,
                        "category_name": cat_data["name"]
                    })
        
        return controls
    
    def get_control_by_id(self, control_id: str) -> Optional[Dict[str, Any]]:
        """Get specific control by ID"""
        for func_id, func_data in self.framework_data.items():
            for cat_id, cat_data in func_data["categories"].items():
                for subcat_id, subcat_desc in cat_data["subcategories"].items():
                    if subcat_id == control_id:
                        return {
                            "id": subcat_id,
                            "description": subcat_desc,
                            "function_id": func_id,
                            "function_name": func_data["name"],
                            "category_id": cat_id,
                            "category_name": cat_data["name"]
                        }
        return None
    
    def get_controls_by_function(self, function_id: str) -> List[Dict[str, Any]]:
        """Get all controls for a specific function"""
        if function_id not in self.framework_data:
            return []
        
        controls = []
        func_data = self.framework_data[function_id]
        
        for cat_id, cat_data in func_data["categories"].items():
            for subcat_id, subcat_desc in cat_data["subcategories"].items():
                controls.append({
                    "id": subcat_id,
                    "description": subcat_desc,
                    "function_id": function_id,
                    "function_name": func_data["name"],
                    "category_id": cat_id,
                    "category_name": cat_data["name"]
                })
        
        return controls
    
    def search_controls(self, query: str) -> List[Dict[str, Any]]:
        """Search controls by description text"""
        query_lower = query.lower()
        matching_controls = []
        
        for control in self.get_all_controls():
            if (query_lower in control["description"].lower() or 
                query_lower in control["function_name"].lower() or
                query_lower in control["category_name"].lower()):
                matching_controls.append(control)
        
        return matching_controls
    
    def validate_control_id(self, control_id: str) -> bool:
        """Validate if a control ID exists in the framework"""
        return self.get_control_by_id(control_id) is not None

# Singleton instance
nist_framework = NISTFrameworkService()