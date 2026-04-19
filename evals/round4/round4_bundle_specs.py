from __future__ import annotations

from evals.round2.build_round2_eval_bundles import supported_line, unsupported_line


def round4_extra_specs() -> list[dict]:
    return [
        {
            "slug": "nimbus_fintech_core_november_2024",
            "company": "Nimbus Fintech Core",
            "summary_expectations": {
                "must_surface_lines": [
                    "Revenue",
                    "Card Network Fees",
                    "Fraud Operations",
                    "Engineering Contractors",
                ],
                "max_opening_drivers": 5,
                "forbid_mixed_total_story": True,
            },
            "accounts": [
                ("Revenue", 890000, 934500),
                ("Card Network Fees", 124000, 148200),
                ("Fraud Operations", 56000, 67800),
                ("Engineering Contractors", 142000, 158900),
                ("Salaries", 310000, 318400),
                ("Software & Subscriptions", 48000, 49200),
                ("Professional Fees", 22000, 22400),
                ("Marketing Programs", 67000, 68100),
                ("Insurance", 19000, 18850),
                ("Travel & Entertainment", 12000, 12300),
            ],
            "mock_context": {
                "search_crm": {
                    "Revenue": {
                        "broad": "CRM renewal board shows two issuer programs expanded interchange share in November worth +28000 versus plan.",
                        "narrow": "Deal desk confirms one enterprise issuer bundle closed a week early after risk sign-off.",
                    }
                },
                "search_gmail": {
                    "Card Network Fees": {
                        "broad": "Network interchange statement shows elevated cross-border ticket volume in the Thanksgiving travel window.",
                    },
                    "Fraud Operations": {
                        "broad": "Ops inbox confirms temporary analyst surge staffing for a coordinated chargeback spike.",
                    },
                },
                "search_slack": {
                    "Revenue": {
                        "narrow": "Commercial thread confirms issuer bundle paperwork finished before November close.",
                    },
                },
                "search_calendar": {
                    "Fraud Operations": {
                        "broad": "Fraud war-room blocks were scheduled nightly for the second week of November.",
                    }
                },
            },
            "oracle_lines": [
                supported_line(
                    "Revenue",
                    890000,
                    934500,
                    "issuer program expansions and an accelerated enterprise bundle lifted november revenue",
                    ["issuer programs", "interchange share", "enterprise issuer bundle", "november"],
                    ["crm", "slack"],
                    ["crm-revenue-broad", "crm-revenue-narrow", "slack-revenue-narrow"],
                ),
                supported_line(
                    "Card Network Fees",
                    124000,
                    148200,
                    "elevated cross-border ticket volume in late november increased network fees",
                    ["cross-border", "ticket volume", "thanksgiving travel"],
                    ["gmail"],
                    ["gmail-card_network_fees-broad"],
                ),
                supported_line(
                    "Fraud Operations",
                    56000,
                    67800,
                    "temporary analyst surge staffing during a chargeback spike drove overtime",
                    ["analyst surge", "chargeback spike", "war-room"],
                    ["gmail", "calendar"],
                    ["gmail-fraud_operations-broad", "calendar-fraud_operations-broad"],
                ),
                unsupported_line("Engineering Contractors", 142000, 158900),
            ],
        },
        {
            "slug": "pacific_seafoods_procurement_november_2024",
            "company": "Pacific Seafoods Procurement",
            "summary_expectations": {
                "must_surface_lines": [
                    "Fresh Catch COGS",
                    "Inbound Freight",
                    "Cold Storage Utilities",
                    "Packaging Supplies",
                ],
                "max_opening_drivers": 5,
                "forbid_mixed_total_story": True,
            },
            "accounts": [
                ("Fresh Catch COGS", 410000, 451200),
                ("Inbound Freight", 88000, 102400),
                ("Cold Storage Utilities", 72000, 83400),
                ("Packaging Supplies", 34000, 38800),
                ("Plant Labor", 198000, 205500),
                ("Professional Fees", 14000, 14200),
                ("Insurance", 16000, 15900),
                ("Software & Subscriptions", 11000, 11250),
                ("Travel & Training", 9000, 9200),
                ("Repairs & Maintenance", 27000, 28500),
            ],
            "mock_context": {
                "search_gmail": {
                    "Fresh Catch COGS": {
                        "broad": "Supplier notice confirms spot pricing on salmon and halibut rose after a coastal storm delayed landings.",
                    },
                    "Inbound Freight": {
                        "broad": "Freight forwarder invoice batch shows emergency airfreight for two delayed reefers.",
                    }
                },
                "search_slack": {
                    "Cold Storage Utilities": {
                        "broad": "Ops channel notes compressor runtime increased while holding extra inventory through the holiday pre-buy.",
                    },
                    "Fresh Catch COGS": {
                        "narrow": "Procurement thread ties the spot buy to a short landing week and higher auction clears.",
                    },
                },
                "search_calendar": {
                    "Inbound Freight": {
                        "broad": "Logistics review with the forwarder was held mid-November after reefer delays.",
                    }
                },
            },
            "oracle_lines": [
                supported_line(
                    "Fresh Catch COGS",
                    410000,
                    451200,
                    "spot pricing on salmon and halibut rose after storm-delayed landings",
                    ["spot pricing", "salmon and halibut", "delayed landings", "auction"],
                    ["gmail", "slack"],
                    ["gmail-fresh_catch_cogs-broad", "slack-fresh_catch_cogs-narrow"],
                ),
                supported_line(
                    "Inbound Freight",
                    88000,
                    102400,
                    "emergency airfreight for delayed reefers increased inbound freight",
                    ["emergency airfreight", "delayed reefers", "forwarder"],
                    ["gmail", "calendar"],
                    ["gmail-inbound_freight-broad", "calendar-inbound_freight-broad"],
                ),
                supported_line(
                    "Cold Storage Utilities",
                    72000,
                    83400,
                    "higher compressor runtime holding extra holiday pre-buy inventory lifted power spend",
                    ["compressor runtime", "extra inventory", "holiday pre-buy"],
                    ["slack"],
                    ["slack-cold_storage_utilities-broad"],
                ),
                unsupported_line("Packaging Supplies", 34000, 38800),
            ],
        },
        {
            "slug": "quartz_business_software_november_2024",
            "company": "Quartz Business Software",
            "summary_expectations": {
                "must_surface_lines": [
                    "Revenue",
                    "R&D Payroll",
                    "Data Center Costs",
                    "Sales Commissions",
                ],
                "max_opening_drivers": 5,
                "forbid_mixed_total_story": True,
            },
            "accounts": [
                ("Revenue", 620000, 668900),
                ("R&D Payroll", 176000, 192400),
                ("Data Center Costs", 98000, 114600),
                ("Sales Commissions", 71000, 84300),
                ("Customer Success Payroll", 134000, 138200),
                ("Professional Fees", 18000, 19600),
                ("Marketing Programs", 52000, 53400),
                ("Software & Subscriptions", 24000, 24700),
                ("Insurance", 21000, 20950),
                ("Travel & Entertainment", 15000, 15200),
            ],
            "mock_context": {
                "search_crm": {
                    "Revenue": {
                        "broad": "CRM shows a platform upsell wave and one healthcare vertical win adding +36000 in November billings.",
                    }
                },
                "search_gmail": {
                    "Data Center Costs": {
                        "broad": "Colo invoice summary shows power draw spike during a zero-downtime cluster migration weekend.",
                    },
                    "R&D Payroll": {
                        "broad": "HR confirms contractor-to-FTE conversions for two backend teams effective mid-November.",
                    },
                },
                "search_slack": {
                    "Sales Commissions": {
                        "broad": "RevOps says commission accruals rose with the healthcare win and upsell wave booked in November.",
                    },
                    "Revenue": {
                        "narrow": "Deal desk confirms healthcare contract signatures landed before month-end.",
                    },
                },
                "search_calendar": {
                    "Data Center Costs": {
                        "broad": "Migration cutover window scheduled overnight Saturday in mid-November.",
                    }
                },
            },
            "oracle_lines": [
                supported_line(
                    "Revenue",
                    620000,
                    668900,
                    "platform upsell wave and a healthcare vertical win lifted november billings",
                    ["platform upsell", "healthcare vertical", "november billings"],
                    ["crm", "slack"],
                    ["crm-revenue-broad", "slack-revenue-narrow"],
                ),
                supported_line(
                    "R&D Payroll",
                    176000,
                    192400,
                    "contractor-to-fte conversions for backend teams increased payroll",
                    ["contractor-to-fte", "backend teams", "mid-november"],
                    ["gmail"],
                    ["gmail-r&d_payroll-broad"],
                ),
                supported_line(
                    "Data Center Costs",
                    98000,
                    114600,
                    "power draw spike during a zero-downtime cluster migration increased colo costs",
                    ["power draw spike", "cluster migration", "colo"],
                    ["gmail", "calendar"],
                    ["gmail-data_center_costs-broad", "calendar-data_center_costs-broad"],
                ),
                supported_line(
                    "Sales Commissions",
                    71000,
                    84300,
                    "commission accruals increased with the healthcare win and upsell bookings",
                    ["commission accruals", "healthcare win", "upsell"],
                    ["slack"],
                    ["slack-sales_commissions-broad"],
                ),
            ],
        },
        {
            "slug": "riverside_logistics_lastmile_november_2024",
            "company": "Riverside Logistics Last Mile",
            "summary_expectations": {
                "must_surface_lines": [
                    "Delivery Labor",
                    "Fuel Surcharges",
                    "Vehicle Leases",
                    "Sortation Equipment",
                ],
                "max_opening_drivers": 5,
                "forbid_mixed_total_story": True,
            },
            "accounts": [
                ("Delivery Labor", 218000, 246800),
                ("Fuel Surcharges", 96000, 112300),
                ("Vehicle Leases", 78000, 82100),
                ("Sortation Equipment", 44000, 51900),
                ("Salaries", 145000, 149200),
                ("Professional Fees", 16000, 16500),
                ("Insurance", 22000, 22300),
                ("Software & Subscriptions", 19000, 19100),
                ("Travel & Entertainment", 8000, 8100),
                ("Repairs & Maintenance", 31000, 32800),
            ],
            "mock_context": {
                "search_gmail": {
                    "Delivery Labor": {
                        "broad": "Staffing vendor summary shows peak Sunday routes and temp sorter coverage for Black Friday week.",
                    },
                    "Vehicle Leases": {
                        "broad": "Fleet email confirms three sprinter leases started early to cover the holiday surge lane.",
                    },
                },
                "search_slack": {
                    "Fuel Surcharges": {
                        "broad": "Ops notes diesel index moved up and surcharge tables were applied to subcontractor routes.",
                    },
                    "Delivery Labor": {
                        "narrow": "Dispatch channel confirms Sunday overtime blocks added for the final November weekend.",
                    },
                },
                "search_calendar": {
                    "Vehicle Leases": {
                        "broad": "Fleet onboarding calendar shows back-to-back vehicle readiness reviews before Black Friday.",
                    }
                },
            },
            "oracle_lines": [
                supported_line(
                    "Delivery Labor",
                    218000,
                    246800,
                    "peak sunday routes and temp sorter coverage for black friday week increased payroll",
                    ["peak sunday routes", "temp sorter", "black friday week"],
                    ["gmail", "slack"],
                    ["gmail-delivery_labor-broad", "slack-delivery_labor-narrow"],
                ),
                supported_line(
                    "Fuel Surcharges",
                    96000,
                    112300,
                    "diesel index movement and applied surcharge tables raised fuel surcharges",
                    ["diesel index", "surcharge tables", "subcontractor routes"],
                    ["slack"],
                    ["slack-fuel_surcharges-broad"],
                ),
                supported_line(
                    "Vehicle Leases",
                    78000,
                    82100,
                    "three sprinter leases started early for the holiday surge lane",
                    ["sprinter leases", "holiday surge lane", "fleet"],
                    ["gmail", "calendar"],
                    ["gmail-vehicle_leases-broad", "calendar-vehicle_leases-broad"],
                ),
                unsupported_line("Sortation Equipment", 44000, 51900),
            ],
        },
        {
            "slug": "summit_clinical_trials_november_2024",
            "company": "Summit Clinical Trials",
            "summary_expectations": {
                "must_surface_lines": [
                    "Site Payments",
                    "Patient Stipends",
                    "Monitoring Fees",
                    "Central Lab Services",
                ],
                "max_opening_drivers": 5,
                "forbid_mixed_total_story": True,
            },
            "accounts": [
                ("Site Payments", 280000, 312500),
                ("Patient Stipends", 42000, 48900),
                ("Monitoring Fees", 67000, 75800),
                ("Central Lab Services", 91000, 98800),
                ("Salaries", 240000, 246000),
                ("Professional Fees", 19000, 20400),
                ("Travel & Training", 28000, 30200),
                ("Software & Subscriptions", 21000, 21200),
                ("Insurance", 17000, 16900),
                ("Office & Facilities", 14000, 14500),
            ],
            "mock_context": {
                "search_gmail": {
                    "Site Payments": {
                        "broad": "CTA inbox shows two sites invoiced milestone payments earlier after accelerated enrollment.",
                    },
                    "Monitoring Fees": {
                        "broad": "CRO email approves extra monitoring visits after a data query backlog opened mid-month.",
                    },
                },
                "search_slack": {
                    "Patient Stipends": {
                        "broad": "Study coordinator channel notes higher stipend volume when weekend visit windows expanded.",
                    },
                    "Site Payments": {
                        "narrow": "Clinical ops confirms milestone triggers aligned with the enrollment acceleration.",
                    },
                },
                "search_calendar": {
                    "Monitoring Fees": {
                        "broad": "Monitoring visit blocks were added on the calendar for week three of November.",
                    }
                },
            },
            "oracle_lines": [
                supported_line(
                    "Site Payments",
                    280000,
                    312500,
                    "accelerated enrollment pulled two site milestone payments into november",
                    ["milestone payments", "accelerated enrollment", "sites"],
                    ["gmail", "slack"],
                    ["gmail-site_payments-broad", "slack-site_payments-narrow"],
                ),
                supported_line(
                    "Patient Stipends",
                    42000,
                    48900,
                    "expanded weekend visit windows increased stipend volume",
                    ["weekend visit windows", "stipend volume", "study coordinator"],
                    ["slack"],
                    ["slack-patient_stipends-broad"],
                ),
                supported_line(
                    "Monitoring Fees",
                    67000,
                    75800,
                    "extra monitoring visits after a data query backlog increased fees",
                    ["extra monitoring visits", "data query backlog", "cro"],
                    ["gmail", "calendar"],
                    ["gmail-monitoring_fees-broad", "calendar-monitoring_fees-broad"],
                ),
                unsupported_line("Central Lab Services", 91000, 98800),
            ],
        },
        {
            "slug": "tundra_retail_operations_november_2024",
            "company": "Tundra Retail Operations",
            "summary_expectations": {
                "must_surface_lines": [
                    "Store Payroll",
                    "Inventory Shrink",
                    "Rent",
                    "Store Supplies",
                ],
                "max_opening_drivers": 5,
                "forbid_mixed_total_story": True,
            },
            "accounts": [
                ("Store Payroll", 410000, 438600),
                ("Inventory Shrink", 28000, 41200),
                ("Rent", 196000, 201400),
                ("Store Supplies", 19000, 24600),
                ("Marketing Programs", 54000, 56200),
                ("Utilities", 62000, 63100),
                ("Professional Fees", 12000, 12100),
                ("Software & Subscriptions", 17000, 17300),
                ("Insurance", 24000, 23900),
                ("Travel & Entertainment", 7000, 6900),
            ],
            "mock_context": {
                "search_gmail": {
                    "Store Payroll": {
                        "broad": "Payroll approval email confirms holiday season temp hiring and overlap with returning students.",
                    },
                    "Rent": {
                        "broad": "Landlord notice shows CAM true-up billed in November for two anchor locations.",
                    },
                },
                "search_slack": {
                    "Inventory Shrink": {
                        "broad": "Loss prevention thread ties november spike to high-theft SKU resets and miscounts during remerch.",
                    },
                    "Store Payroll": {
                        "narrow": "Store ops confirms overlap shifts for the Black Friday weekend schedule.",
                    },
                },
                "search_calendar": {
                    "Rent": {
                        "broad": "Lease admin review for CAM true-up scheduled the week before Thanksgiving.",
                    }
                },
            },
            "oracle_lines": [
                supported_line(
                    "Store Payroll",
                    410000,
                    438600,
                    "holiday temp hiring and overlap with returning students increased payroll",
                    ["temp hiring", "returning students", "overlap shifts"],
                    ["gmail", "slack"],
                    ["gmail-store_payroll-broad", "slack-store_payroll-narrow"],
                ),
                supported_line(
                    "Inventory Shrink",
                    28000,
                    41200,
                    "high-theft sku resets and miscounts during remerch drove shrink higher",
                    ["high-theft sku", "miscounts", "remerch", "loss prevention"],
                    ["slack"],
                    ["slack-inventory_shrink-broad"],
                ),
                supported_line(
                    "Rent",
                    196000,
                    201400,
                    "cam true-up for two anchor locations billed in november increased rent",
                    ["cam true-up", "anchor locations", "landlord"],
                    ["gmail", "calendar"],
                    ["gmail-rent-broad", "calendar-rent-broad"],
                ),
                unsupported_line("Store Supplies", 19000, 24600),
            ],
        },
        {
            "slug": "vantage_cyber_defense_november_2024",
            "company": "Vantage Cyber Defense",
            "summary_expectations": {
                "must_surface_lines": [
                    "MRR Revenue",
                    "SOC Staffing",
                    "Threat Intel Feeds",
                    "Incident Response Retainer",
                ],
                "max_opening_drivers": 5,
                "forbid_mixed_total_story": True,
            },
            "accounts": [
                ("MRR Revenue", 540000, 578200),
                ("SOC Staffing", 198000, 215400),
                ("Threat Intel Feeds", 46000, 54800),
                ("Incident Response Retainer", 32000, 34800),
                ("Professional Fees", 24000, 26200),
                ("Software & Subscriptions", 31000, 31800),
                ("Travel & Entertainment", 11000, 10800),
                ("Marketing Programs", 38000, 39200),
                ("Insurance", 15000, 15100),
                ("Office & Facilities", 13000, 13200),
            ],
            "mock_context": {
                "search_crm": {
                    "MRR Revenue": {
                        "broad": "CRM renewal schedule shows three enterprise MSSP expansions effective in November.",
                    }
                },
                "search_gmail": {
                    "Threat Intel Feeds": {
                        "broad": "Vendor notice confirms upgraded threat feed bundle after a regulator inquiry template change.",
                    },
                    "SOC Staffing": {
                        "broad": "Staffing memo approves weekend analyst overlap during a red-team exercise window.",
                    },
                },
                "search_slack": {
                    "SOC Staffing": {
                        "narrow": "SOC lead confirms shift overlap covered the red-team exercise weekend.",
                    },
                    "MRR Revenue": {
                        "narrow": "Customer success confirms MSSP expansions were activated on schedule.",
                    },
                },
                "search_calendar": {
                    "Threat Intel Feeds": {
                        "broad": "Vendor enablement session for the upgraded feed bundle held mid-November.",
                    }
                },
            },
            "oracle_lines": [
                supported_line(
                    "MRR Revenue",
                    540000,
                    578200,
                    "three enterprise mssp expansions effective in november lifted mrr",
                    ["enterprise mssp expansions", "november", "renewal schedule"],
                    ["crm", "slack"],
                    ["crm-mrr_revenue-broad", "slack-mrr_revenue-narrow"],
                ),
                supported_line(
                    "SOC Staffing",
                    198000,
                    215400,
                    "weekend analyst overlap during a red-team exercise increased soc payroll",
                    ["weekend analyst overlap", "red-team exercise", "shift overlap"],
                    ["gmail", "slack"],
                    ["gmail-soc_staffing-broad", "slack-soc_staffing-narrow"],
                ),
                supported_line(
                    "Threat Intel Feeds",
                    46000,
                    54800,
                    "upgraded threat feed bundle after a regulator inquiry template change increased cost",
                    ["upgraded threat feed bundle", "regulator inquiry", "vendor"],
                    ["gmail", "calendar"],
                    ["gmail-threat_intel_feeds-broad", "calendar-threat_intel_feeds-broad"],
                ),
                unsupported_line("Incident Response Retainer", 32000, 34800),
            ],
        },
        {
            "slug": "willow_ag_supply_november_2024",
            "company": "Willow Ag Supply",
            "summary_expectations": {
                "must_surface_lines": [
                    "Grain Purchases",
                    "Agronomy Services",
                    "Equipment Rental",
                    "Seasonal Fuel",
                ],
                "max_opening_drivers": 5,
                "forbid_mixed_total_story": True,
            },
            "accounts": [
                ("Grain Purchases", 520000, 561400),
                ("Agronomy Services", 76000, 88200),
                ("Equipment Rental", 94000, 108900),
                ("Seasonal Fuel", 118000, 129600),
                ("Salaries", 172000, 176800),
                ("Professional Fees", 11000, 11300),
                ("Insurance", 14000, 13950),
                ("Software & Subscriptions", 9000, 9150),
                ("Travel & Training", 13000, 13400),
                ("Repairs & Maintenance", 21000, 22300),
            ],
            "mock_context": {
                "search_gmail": {
                    "Grain Purchases": {
                        "broad": "Co-op bulletin confirms basis rally and deferred contract pricing closed higher in mid-November.",
                    },
                    "Equipment Rental": {
                        "broad": "Rental invoice packet shows extra combine headers for a wet harvest window.",
                    },
                },
                "search_slack": {
                    "Agronomy Services": {
                        "broad": "Agronomy desk notes soil sampling rush and late-season nutrient applications before freeze.",
                    },
                    "Grain Purchases": {
                        "narrow": "Trading desk confirms deferred contracts priced into the november position.",
                    },
                },
                "search_calendar": {
                    "Equipment Rental": {
                        "broad": "Field ops scheduled equipment swaps daily during the wet harvest stretch.",
                    }
                },
            },
            "oracle_lines": [
                supported_line(
                    "Grain Purchases",
                    520000,
                    561400,
                    "basis rally and deferred contract pricing closed higher mid-month",
                    ["basis rally", "deferred contract", "mid-november", "co-op"],
                    ["gmail", "slack"],
                    ["gmail-grain_purchases-broad", "slack-grain_purchases-narrow"],
                ),
                supported_line(
                    "Agronomy Services",
                    76000,
                    88200,
                    "soil sampling rush and late-season nutrient applications increased agronomy spend",
                    ["soil sampling rush", "nutrient applications", "before freeze"],
                    ["slack"],
                    ["slack-agronomy_services-broad"],
                ),
                supported_line(
                    "Equipment Rental",
                    94000,
                    108900,
                    "extra combine headers for a wet harvest window drove rental cost",
                    ["combine headers", "wet harvest", "rental invoice"],
                    ["gmail", "calendar"],
                    ["gmail-equipment_rental-broad", "calendar-equipment_rental-broad"],
                ),
                unsupported_line("Seasonal Fuel", 118000, 129600),
            ],
        },
        {
            "slug": "zenith_broadcast_network_november_2024",
            "company": "Zenith Broadcast Network",
            "summary_expectations": {
                "must_surface_lines": [
                    "Ad Revenue",
                    "Program Production",
                    "Tower Lease Costs",
                    "Content Royalties",
                ],
                "max_opening_drivers": 5,
                "forbid_mixed_total_story": True,
            },
            "accounts": [
                ("Ad Revenue", 710000, 748900),
                ("Program Production", 134000, 156200),
                ("Tower Lease Costs", 88000, 92300),
                ("Content Royalties", 52000, 61100),
                ("Salaries", 265000, 271400),
                ("Professional Fees", 21000, 22800),
                ("Marketing Programs", 48000, 49500),
                ("Software & Subscriptions", 26000, 26400),
                ("Insurance", 18000, 17950),
                ("Travel & Entertainment", 16000, 16200),
            ],
            "mock_context": {
                "search_crm": {
                    "Ad Revenue": {
                        "broad": "CRM scatter market report shows political flight added +31000 in November spot revenue.",
                    }
                },
                "search_gmail": {
                    "Program Production": {
                        "broad": "Production finance confirms unplanned overtime for election-night coverage and satellite uplinks.",
                    },
                    "Tower Lease Costs": {
                        "broad": "Lease operations email notes CPI step-up on two tower agreements effective November 1.",
                    },
                },
                "search_slack": {
                    "Program Production": {
                        "narrow": "Control room thread confirms extended cutdown sessions after the debate replay package.",
                    },
                    "Ad Revenue": {
                        "narrow": "Sales ops confirms political flight booked into november spot logs.",
                    },
                },
                "search_calendar": {
                    "Tower Lease Costs": {
                        "broad": "Lease admin review for CPI step-up held the first week of November.",
                    }
                },
            },
            "oracle_lines": [
                supported_line(
                    "Ad Revenue",
                    710000,
                    748900,
                    "political flight added november spot revenue in the scatter market",
                    ["political flight", "spot revenue", "scatter market"],
                    ["crm", "slack"],
                    ["crm-ad_revenue-broad", "slack-ad_revenue-narrow"],
                ),
                supported_line(
                    "Program Production",
                    134000,
                    156200,
                    "unplanned overtime for election-night coverage and satellite uplinks increased production cost",
                    ["election-night coverage", "satellite uplinks", "overtime"],
                    ["gmail", "slack"],
                    ["gmail-program_production-broad", "slack-program_production-narrow"],
                ),
                supported_line(
                    "Tower Lease Costs",
                    88000,
                    92300,
                    "cpi step-up on two tower agreements effective november 1 increased lease expense",
                    ["cpi step-up", "tower agreements", "november 1"],
                    ["gmail", "calendar"],
                    ["gmail-tower_lease_costs-broad", "calendar-tower_lease_costs-broad"],
                ),
                unsupported_line("Content Royalties", 52000, 61100),
            ],
        },
    ]
