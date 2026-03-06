# OASF Taxonomy v0.8.0

Open Agentic Schema Framework - standardized skills (136) and domains (204) for agent classification. Use slash-separated slugs with `agent.addSkill()` / `agent.addDomain()`.

Source: https://github.com/agntcy/oasf

## Skills (136 total)

### advanced_reasoning_planning

| Slug | Description |
|------|-------------|
| `advanced_reasoning_planning/advanced_reasoning_planning` | (category root) |
| `advanced_reasoning_planning/chain_of_thought_structuring` | Organizing intermediate reasoning steps into clear, justifiable sequences |
| `advanced_reasoning_planning/hypothesis_generation` | Proposing plausible explanations or solution pathways for incomplete or uncertain scenarios |
| `advanced_reasoning_planning/long_horizon_reasoning` | Maintaining coherent reasoning chains over extended sequences of steps or time |
| `advanced_reasoning_planning/strategic_planning` | Formulating high-level multi-phase strategies aligned with long-term objectives |

### agent_orchestration

| Slug | Description |
|------|-------------|
| `agent_orchestration/agent_orchestration` | (category root) |
| `agent_orchestration/agent_coordination` | Managing real-time collaboration and state synchronization among agents |
| `agent_orchestration/multi_agent_planning` | Coordinating plans across multiple agents, resolving dependencies and optimizing sequencing |
| `agent_orchestration/negotiation_resolution` | Facilitating negotiation, conflict handling, and consensus-building between agents |
| `agent_orchestration/role_assignment` | Allocating responsibilities to agents based on capabilities and task requirements |
| `agent_orchestration/task_decomposition` | Breaking complex objectives into structured, atomic subtasks |

### analytical_skills

| Slug | Description |
|------|-------------|
| `analytical_skills/analytical_skills` | (category root) |
| `analytical_skills/coding_skills/coding_skills` | Capabilities for code generation, documentation, and optimization |
| `analytical_skills/coding_skills/code_optimization` | Rewriting and optimizing existing code through refactoring techniques |
| `analytical_skills/coding_skills/code_templates` | Automatically filling in code templates with appropriate content |
| `analytical_skills/coding_skills/code_to_docstrings` | Generating natural language documentation for code segments |
| `analytical_skills/coding_skills/text_to_code` | Translating natural language instructions into executable code |
| `analytical_skills/mathematical_reasoning/mathematical_reasoning` | Capabilities for solving mathematical problems and proving theorems |
| `analytical_skills/mathematical_reasoning/geometry` | Solving geometric problems and spatial reasoning tasks |
| `analytical_skills/mathematical_reasoning/math_word_problems` | Solving mathematical exercises presented in natural language format |
| `analytical_skills/mathematical_reasoning/pure_math_operations` | Executing pure mathematical operations, such as arithmetic calculations |
| `analytical_skills/mathematical_reasoning/theorem_proving` | Proving mathematical theorems using computational methods |

### audio

| Slug | Description |
|------|-------------|
| `audio/audio` | (category root) |
| `audio/audio_classification` | Assigning labels or classes to audio content based on its characteristics |
| `audio/audio_to_audio` | Transforming audio through various manipulations including cutting, filtering, and mixing |

### data_engineering

| Slug | Description |
|------|-------------|
| `data_engineering/data_engineering` | (category root) |
| `data_engineering/data_cleaning` | Detecting and correcting errors, inconsistencies, and missing values |
| `data_engineering/data_quality_assessment` | Evaluating datasets for completeness, validity, consistency, and timeliness |
| `data_engineering/data_transformation_pipeline` | Designing multi-step sequences that extract, transform, and load datasets |
| `data_engineering/feature_engineering` | Constructing informative transformed variables to improve model performance |
| `data_engineering/schema_inference` | Deriving structural metadata (fields, types, relationships) from raw data |

### devops_mlops

| Slug | Description |
|------|-------------|
| `devops_mlops/devops_mlops` | (category root) |
| `devops_mlops/ci_cd_configuration` | Designing or modifying continuous integration and delivery workflows |
| `devops_mlops/deployment_orchestration` | Coordinating multi-stage deployments, rollbacks, and version transitions |
| `devops_mlops/infrastructure_provisioning` | Allocating and configuring compute, storage, and networking resources |
| `devops_mlops/model_versioning` | Tracking, promoting, and documenting different iterations of models |
| `devops_mlops/monitoring_alerting` | Configuring and interpreting telemetry signals, thresholds, and alerts |

### evaluation_monitoring

| Slug | Description |
|------|-------------|
| `evaluation_monitoring/evaluation_monitoring` | (category root) |
| `evaluation_monitoring/anomaly_detection` | Identifying unusual patterns, drifts, or deviations in data or model outputs |
| `evaluation_monitoring/benchmark_execution` | Running standardized benchmarks or evaluation suites |
| `evaluation_monitoring/performance_monitoring` | Tracking latency, throughput, resource utilization, and reliability |
| `evaluation_monitoring/quality_evaluation` | Assessing outputs for accuracy, relevance, coherence, safety, and style |
| `evaluation_monitoring/test_case_generation` | Creating targeted test inputs or scenarios to probe system behavior |

### governance_compliance

| Slug | Description |
|------|-------------|
| `governance_compliance/governance_compliance` | (category root) |
| `governance_compliance/audit_trail_summarization` | Condensing event/transaction logs into human-readable compliance summaries |
| `governance_compliance/compliance_assessment` | Evaluating against standards (GDPR, HIPAA) and identifying gaps |
| `governance_compliance/policy_mapping` | Translating policies into structured, enforceable rules or checklists |
| `governance_compliance/risk_classification` | Categorizing risks by impact and likelihood for prioritization |

### images_computer_vision

| Slug | Description |
|------|-------------|
| `images_computer_vision/images_computer_vision` | (category root) |
| `images_computer_vision/depth_estimation` | Predicting distance or depth of objects within a scene |
| `images_computer_vision/image_classification` | Assigning labels or categories to images |
| `images_computer_vision/image_feature_extraction` | Identifying and isolating key characteristics from images |
| `images_computer_vision/image_generation` | Creating new images from learned patterns |
| `images_computer_vision/image_segmentation` | Pixel-level classification of image regions |
| `images_computer_vision/image_to_3d` | Converting 2D images into 3D representations |
| `images_computer_vision/image_to_image` | Transforming images (style transfer, colorization, enhancement) |
| `images_computer_vision/keypoint_detection` | Identifying specific points of interest within images |
| `images_computer_vision/mask_generation` | Producing segmented regions to highlight specific areas |
| `images_computer_vision/object_detection` | Identifying and locating objects with bounding boxes |
| `images_computer_vision/video_classification` | Assigning labels to videos or segments |

### multi_modal

| Slug | Description |
|------|-------------|
| `multi_modal/multi_modal` | (category root) |
| `multi_modal/any_to_any` | Converting between any supported modalities |
| `multi_modal/audio_processing/audio_processing` | Audio processing capabilities |
| `multi_modal/audio_processing/speech_recognition` | Converting spoken language into written text |
| `multi_modal/audio_processing/text_to_speech` | Converting text into natural-sounding speech |
| `multi_modal/image_processing/image_processing` | Image processing and generation capabilities |
| `multi_modal/image_processing/image_to_text` | Generating textual descriptions for images |
| `multi_modal/image_processing/text_to_3d` | Generating 3D objects from text descriptions |
| `multi_modal/image_processing/text_to_image` | Generating images from text descriptions |
| `multi_modal/image_processing/text_to_video` | Generating video from text descriptions |
| `multi_modal/image_processing/visual_qa` | Answering questions about images |

### natural_language_processing

| Slug | Description |
|------|-------------|
| `natural_language_processing/natural_language_processing` | (category root) |
| **analytical_reasoning** | |
| `natural_language_processing/analytical_reasoning/analytical_reasoning` | Logical analysis, inference, and problem-solving |
| `natural_language_processing/analytical_reasoning/fact_verification` | Verifying facts and claims given reference text |
| `natural_language_processing/analytical_reasoning/inference_deduction` | Making logical inferences from provided information |
| `natural_language_processing/analytical_reasoning/problem_solving` | Generating potential solutions or strategies |
| **creative_content** | |
| `natural_language_processing/creative_content/creative_content` | Creative content generation |
| `natural_language_processing/creative_content/poetry_writing` | Composing poems, prose, or creative literature |
| `natural_language_processing/creative_content/storytelling` | Creating narratives and fictional content |
| **ethical_interaction** | |
| `natural_language_processing/ethical_interaction/ethical_interaction` | Ethical and safe interaction |
| `natural_language_processing/ethical_interaction/bias_mitigation` | Reducing biased language, ensuring fair output |
| `natural_language_processing/ethical_interaction/content_moderation` | Avoiding harmful or inappropriate content |
| **feature_extraction** | |
| `natural_language_processing/feature_extraction/feature_extraction` | Textual feature extraction |
| `natural_language_processing/feature_extraction/model_feature_extraction` | Representing text as vectors for downstream tasks |
| **information_retrieval_synthesis** | |
| `natural_language_processing/information_retrieval_synthesis/information_retrieval_synthesis` | Information retrieval and synthesis |
| `natural_language_processing/information_retrieval_synthesis/document_passage_retrieval` | Retrieving relevant documents or passages |
| `natural_language_processing/information_retrieval_synthesis/fact_extraction` | Extracting factual information from text |
| `natural_language_processing/information_retrieval_synthesis/knowledge_synthesis` | Aggregating information from multiple sources |
| `natural_language_processing/information_retrieval_synthesis/question_answering` | Understanding questions and providing answers |
| `natural_language_processing/information_retrieval_synthesis/search` | Efficient search within textual databases |
| `natural_language_processing/information_retrieval_synthesis/sentence_similarity` | Determining semantic similarity between sentences |
| **language_translation** | |
| `natural_language_processing/language_translation/language_translation` | Translation and multilingual support |
| `natural_language_processing/language_translation/multilingual_understanding` | Processing text in multiple languages |
| `natural_language_processing/language_translation/translation` | Converting text between languages |
| **natural_language_generation** | |
| `natural_language_processing/natural_language_generation/natural_language_generation` | Text generation from data or inputs |
| `natural_language_processing/natural_language_generation/dialogue_generation` | Producing conversational responses |
| `natural_language_processing/natural_language_generation/paraphrasing` | Rewriting text with different words, same meaning |
| `natural_language_processing/natural_language_generation/question_generation` | Generating questions from text |
| `natural_language_processing/natural_language_generation/story_generation` | Generating text from a description or first sentence |
| `natural_language_processing/natural_language_generation/style_transfer` | Rewriting text to match a given style |
| `natural_language_processing/natural_language_generation/summarization` | Condensing text while preserving essential information |
| `natural_language_processing/natural_language_generation/text_completion` | Continuing text in a coherent manner |
| **natural_language_understanding** | |
| `natural_language_processing/natural_language_understanding/natural_language_understanding` | Interpreting and comprehending language |
| `natural_language_processing/natural_language_understanding/contextual_comprehension` | Understanding context and nuances |
| `natural_language_processing/natural_language_understanding/entity_recognition` | Identifying key entities (names, dates, locations) |
| `natural_language_processing/natural_language_understanding/semantic_understanding` | Grasping meaning and intent |
| **personalization** | |
| `natural_language_processing/personalization/personalization` | Personalisation and adaptation |
| `natural_language_processing/personalization/style_adjustment` | Modifying tone or style for specific audiences |
| `natural_language_processing/personalization/user_adaptation` | Tailoring responses based on user preferences |
| **text_classification** | |
| `natural_language_processing/text_classification/text_classification` | Text classification and categorization |
| `natural_language_processing/text_classification/natural_language_inference` | Classifying relations between texts (contradiction, entailment) |
| `natural_language_processing/text_classification/sentiment_analysis` | Classifying sentiment of text |
| `natural_language_processing/text_classification/topic_labeling` | Classifying text by topic |
| **token_classification** | |
| `natural_language_processing/token_classification/token_classification` | Token-level classification |
| `natural_language_processing/token_classification/named_entity_recognition` | Recognizing named entities |
| `natural_language_processing/token_classification/pos_tagging` | Part-of-speech tagging |

### retrieval_augmented_generation

| Slug | Description |
|------|-------------|
| `retrieval_augmented_generation/retrieval_augmented_generation` | (category root) |
| `retrieval_augmented_generation/document_or_database_question_answering` | Retrieving info from documents/databases to answer questions |
| `retrieval_augmented_generation/generation_of_any` | Augmenting creation of text/images/audio with retrieved information |
| `retrieval_augmented_generation/retrieval_of_information/retrieval_of_information` | Fetching relevant data from datasets |
| `retrieval_augmented_generation/retrieval_of_information/document_retrieval` | Retrieving relevant documents from collections |
| `retrieval_augmented_generation/retrieval_of_information/indexing` | Indexing data for efficient retrieval |
| `retrieval_augmented_generation/retrieval_of_information/search` | Exploring datasets to find relevant information |

### security_privacy

| Slug | Description |
|------|-------------|
| `security_privacy/security_privacy` | (category root) |
| `security_privacy/privacy_risk_assessment` | Evaluating data handling for potential privacy risks |
| `security_privacy/secret_leak_detection` | Scanning for exposed credentials, tokens, or secrets |
| `security_privacy/threat_detection` | Identifying indicators of malicious activity |
| `security_privacy/vulnerability_analysis` | Reviewing code/configs for security weaknesses |

### tabular_text

| Slug | Description |
|------|-------------|
| `tabular_text/tabular_text` | (category root) |
| `tabular_text/tabular_classification` | Classifying data based on tabular attributes |
| `tabular_text/tabular_regression` | Predicting numerical values from tabular features |

### tool_interaction

| Slug | Description |
|------|-------------|
| `tool_interaction/tool_interaction` | (category root) |
| `tool_interaction/api_schema_understanding` | Interpreting API specs, endpoints, parameters |
| `tool_interaction/script_integration` | Linking scripts with external tools |
| `tool_interaction/tool_use_planning` | Selecting and ordering tool invocations |
| `tool_interaction/workflow_automation` | Designing automated multi-tool sequences |

---

## Domains (204 total)

### agriculture

| Slug | Description |
|------|-------------|
| `agriculture/agriculture` | (category root) |
| `agriculture/agricultural_technology` | Drones, IoT, and automation in farming |
| `agriculture/crop_management` | Planning, monitoring, and optimizing crop production |
| `agriculture/livestock_management` | Care, breeding, and management of farm animals |
| `agriculture/precision_agriculture` | Data-driven farming using sensors, GPS, and analytics |
| `agriculture/sustainable_farming` | Environmentally responsible agricultural practices |

### education

| Slug | Description |
|------|-------------|
| `education/education` | (category root) |
| `education/curriculum_design` | Creating structured educational content |
| `education/e_learning` | Digital platforms and online courses |
| `education/educational_technology` | Digital tools to enhance teaching and learning |
| `education/learning_management_systems` | Software for delivering and tracking courses |
| `education/pedagogy` | Methods and practices of teaching |

### energy

| Slug | Description |
|------|-------------|
| `energy/energy` | (category root) |
| `energy/energy_management` | Optimization of energy consumption and efficiency |
| `energy/energy_storage` | Battery systems, pumped hydro, and storage tech |
| `energy/oil_and_gas` | Exploration, extraction, refining, and distribution |
| `energy/power_generation` | Electricity generation from various sources |
| `energy/renewable_energy` | Solar, wind, hydro, and sustainable energy |
| `energy/smart_grids` | Intelligent power distribution networks |

### environmental_science

| Slug | Description |
|------|-------------|
| `environmental_science/environmental_science` | (category root) |
| `environmental_science/climate_science` | Climate modeling, change research, atmospheric science |
| `environmental_science/conservation_biology` | Species conservation, habitat protection, biodiversity |
| `environmental_science/ecology` | Ecosystem science, ecological modeling |
| `environmental_science/environmental_monitoring` | Air/water quality, pollution tracking |
| `environmental_science/environmental_policy` | Regulations, policy development, environmental law |
| `environmental_science/sustainability` | Carbon footprint reduction, circular economy, green tech |

### finance_and_business

| Slug | Description |
|------|-------------|
| `finance_and_business/finance_and_business` | (category root) |
| `finance_and_business/banking` | Retail, investment, corporate, and digital banking |
| `finance_and_business/consumer_goods` | Product development, consumer behavior, marketing |
| `finance_and_business/finance` | Corporate finance, risk management, accounting |
| `finance_and_business/investment_services` | Asset management, advisory, financial planning |
| `finance_and_business/retail` | E-commerce, in-store, inventory, omnichannel |

### government_and_public_sector

| Slug | Description |
|------|-------------|
| `government_and_public_sector/government_and_public_sector` | (category root) |
| `government_and_public_sector/civic_engagement` | Citizen participation, community outreach |
| `government_and_public_sector/e_government` | Digital government services and portals |
| `government_and_public_sector/emergency_management` | Disaster response, crisis management |
| `government_and_public_sector/public_administration` | Government operations, civil service |
| `government_and_public_sector/public_infrastructure` | Infrastructure planning, public works |
| `government_and_public_sector/public_policy` | Policy development, legislative processes |

### healthcare

| Slug | Description |
|------|-------------|
| `healthcare/healthcare` | (category root) |
| `healthcare/health_information_systems` | Systems for managing healthcare data |
| `healthcare/healthcare_informatics` | Health data analytics, clinical informatics |
| `healthcare/medical_technology` | Medical devices, diagnostics, wearable health tech |
| `healthcare/patient_management_systems` | Scheduling, portals, billing, health records |
| `healthcare/telemedicine` | Remote consultation, telehealth platforms |

### hospitality_and_tourism

| Slug | Description |
|------|-------------|
| `hospitality_and_tourism/hospitality_and_tourism` | (category root) |
| `hospitality_and_tourism/event_planning` | Conference management, venue coordination |
| `hospitality_and_tourism/food_and_beverage` | Restaurant management, catering, menu planning |
| `hospitality_and_tourism/hospitality_technology` | PMS, booking engines, guest experience platforms |
| `hospitality_and_tourism/hotel_management` | Hotel operations, reservations, guest services |
| `hospitality_and_tourism/tourism_management` | Destinations, attractions, tourism marketing |
| `hospitality_and_tourism/travel_services` | Travel booking, itinerary planning |

### human_resources

| Slug | Description |
|------|-------------|
| `human_resources/human_resources` | (category root) |
| `human_resources/compensation_and_benefits` | Salary structures, bonuses, benefits |
| `human_resources/employee_relations` | Conflict resolution, engagement, workplace culture |
| `human_resources/hr_analytics` | People analytics, workforce metrics |
| `human_resources/recruitment` | Talent acquisition, sourcing, onboarding |
| `human_resources/training_and_development` | Skills training, leadership development |

### industrial_manufacturing

| Slug | Description |
|------|-------------|
| `industrial_manufacturing/industrial_manufacturing` | (category root) |
| `industrial_manufacturing/automation` | Automated manufacturing, control systems, industrial IoT |
| `industrial_manufacturing/lean_manufacturing` | Continuous improvement, Six Sigma, Kaizen |
| `industrial_manufacturing/process_engineering` | Process design, optimization, quality control |
| `industrial_manufacturing/robotics` | Industrial robotics, RPA, collaborative robots |
| `industrial_manufacturing/supply_chain_management` | Inventory, procurement, logistics, demand forecasting |

### insurance

| Slug | Description |
|------|-------------|
| `insurance/insurance` | (category root) |
| `insurance/actuarial_science` | Risk modeling, statistical modeling, pricing |
| `insurance/claims_processing` | Claims management, loss adjustment, automation |
| `insurance/insurance_sales` | Agent management, distribution, customer acquisition |
| `insurance/insurtech` | Digital insurance platforms, telematics, innovation |
| `insurance/policy_management` | Policy administration, renewals, endorsements |
| `insurance/underwriting` | Risk assessment, policy pricing, automation |

### legal

| Slug | Description |
|------|-------------|
| `legal/legal` | (category root) |
| `legal/contract_law` | Agreements and contracts between parties |
| `legal/corporate_governance` | Directing and controlling corporations |
| `legal/intellectual_property` | Patents, trademarks, copyrights, trade secrets |
| `legal/legal_research` | Precedents, statutes, and case law |
| `legal/litigation` | Legal proceedings and dispute resolution |
| `legal/regulatory_compliance` | Adherence to laws and industry standards |

### life_science

| Slug | Description |
|------|-------------|
| `life_science/life_science` | (category root) |
| `life_science/bioinformatics` | Computational analysis of biological data |
| `life_science/biotechnology` | Biological systems for products and technologies |
| `life_science/genomics` | Genetic structure, function, and evolution |
| `life_science/molecular_biology` | DNA, RNA, proteins, and cell signaling |
| `life_science/pharmaceutical_research` | Drug discovery, clinical trials, pharmacology |

### marketing_and_advertising

| Slug | Description |
|------|-------------|
| `marketing_and_advertising/marketing_and_advertising` | (category root) |
| `marketing_and_advertising/advertising` | Ad campaigns, media buying, creative development |
| `marketing_and_advertising/brand_management` | Brand strategy, identity, positioning |
| `marketing_and_advertising/digital_marketing` | SEO, SEM, content marketing, social media |
| `marketing_and_advertising/market_research` | Consumer research, competitive intelligence |
| `marketing_and_advertising/marketing_analytics` | Metrics, ROI analysis, attribution modeling |
| `marketing_and_advertising/marketing_automation` | Campaign automation, lead nurturing |

### media_and_entertainment

| Slug | Description |
|------|-------------|
| `media_and_entertainment/media_and_entertainment` | (category root) |
| `media_and_entertainment/broadcasting` | Radio and television systems |
| `media_and_entertainment/content_creation` | Video, audio, and written media production |
| `media_and_entertainment/digital_media` | Social media, blogs, podcasts |
| `media_and_entertainment/gaming` | Video game development, esports |
| `media_and_entertainment/publishing` | Book, magazine, and digital publishing |
| `media_and_entertainment/streaming_services` | On-demand video and audio platforms |

### real_estate

| Slug | Description |
|------|-------------|
| `real_estate/real_estate` | (category root) |
| `real_estate/construction` | Building construction and project management |
| `real_estate/facilities_management` | Building operations and maintenance |
| `real_estate/property_management` | Residential and commercial property management |
| `real_estate/proptech` | Smart buildings and real estate platforms |
| `real_estate/real_estate_investment` | Investment strategies and portfolio management |
| `real_estate/urban_planning` | City planning, zoning, urban development |

### research_and_development

| Slug | Description |
|------|-------------|
| `research_and_development/research_and_development` | (category root) |
| `research_and_development/grant_management` | Research funding, grant applications |
| `research_and_development/innovation_management` | Innovation processes, technology transfer |
| `research_and_development/laboratory_management` | Lab operations, equipment, safety protocols |
| `research_and_development/product_development` | Product design, prototyping, testing |
| `research_and_development/research_data_management` | Data storage, research databases, sharing |
| `research_and_development/scientific_research` | Methodology, experimental design, data collection |

### retail_and_ecommerce

| Slug | Description |
|------|-------------|
| `retail_and_ecommerce/retail_and_ecommerce` | (category root) |
| `retail_and_ecommerce/customer_experience` | Personalization, loyalty, shopping optimization |
| `retail_and_ecommerce/inventory_management` | Stock control, warehouse management |
| `retail_and_ecommerce/online_retail` | E-commerce platforms, digital marketplaces |
| `retail_and_ecommerce/order_fulfillment` | Order processing, shipping, returns |
| `retail_and_ecommerce/point_of_sale` | POS systems, payment processing |
| `retail_and_ecommerce/retail_analytics` | Sales analytics, customer insights |

### social_services

| Slug | Description |
|------|-------------|
| `social_services/social_services` | (category root) |
| `social_services/case_management` | Client case tracking, service coordination |
| `social_services/child_and_family_services` | Child welfare, foster care, adoption |
| `social_services/community_outreach` | Community programs and engagement |
| `social_services/disability_services` | Disability support, accessibility, assistive technology |
| `social_services/housing_assistance` | Homeless services, emergency shelter |
| `social_services/mental_health_services` | Counseling, crisis intervention |

### sports_and_fitness

| Slug | Description |
|------|-------------|
| `sports_and_fitness/sports_and_fitness` | (category root) |
| `sports_and_fitness/athletic_training` | Performance training, coaching, athlete development |
| `sports_and_fitness/fitness_and_wellness` | Fitness programs, wellness coaching |
| `sports_and_fitness/sports_analytics` | Performance metrics, game analysis |
| `sports_and_fitness/sports_management` | Team management, facilities, event organization |
| `sports_and_fitness/sports_medicine` | Injury prevention, rehabilitation |
| `sports_and_fitness/sports_technology` | Wearables, performance tracking systems |

### technology

| Slug | Description |
|------|-------------|
| `technology/technology` | (category root) |
| **automation** | |
| `technology/automation/automation` | Process automation with minimal human intervention |
| `technology/automation/rpa` | Robotic Process Automation for repetitive tasks |
| `technology/automation/workflow_automation` | Automated business process sequences |
| **blockchain** | |
| `technology/blockchain/blockchain` | Distributed ledger technology |
| `technology/blockchain/cryptocurrency` | Digital currency secured by cryptography |
| `technology/blockchain/defi` | Decentralized finance services on blockchain |
| `technology/blockchain/smart_contracts` | Self-executing contracts on blockchain |
| **cloud_computing** | |
| `technology/cloud_computing/cloud_computing` | Computing services over the internet |
| `technology/cloud_computing/aws` | Amazon Web Services |
| `technology/cloud_computing/azure` | Microsoft Azure |
| `technology/cloud_computing/gcp` | Google Cloud Platform |
| **communication_systems** | |
| `technology/communication_systems/communication_systems` | Information transmission technologies |
| `technology/communication_systems/broadcasting_systems` | Distributing content to large audiences |
| `technology/communication_systems/signal_processing` | Analysis and modification of signals |
| `technology/communication_systems/telecommunication` | Long-distance information transmission |
| `technology/communication_systems/wireless_communication` | Communication without physical connections |
| **data_science** | |
| `technology/data_science/data_science` | Extracting insights from data |
| `technology/data_science/big_data` | Large/complex datasets requiring advanced tools |
| `technology/data_science/data_engineering` | Systems for collecting, storing, processing data |
| `technology/data_science/data_visualization` | Graphical representation of data |
| **information_technology** | |
| `technology/information_technology/information_technology` | Managing technology systems |
| `technology/information_technology/database_administration` | Database management and maintenance |
| `technology/information_technology/help_desk_support` | Technical support for end users |
| `technology/information_technology/performance_analysis` | System performance optimization |
| `technology/information_technology/system_administration` | Computer systems and servers management |
| **iot** | |
| `technology/iot/iot` | Internet of Things |
| `technology/iot/industrial_iot` | IoT in industrial settings |
| `technology/iot/iot_devices` | Devices with sensors and connectivity |
| `technology/iot/iot_networks` | Communication protocols for IoT |
| `technology/iot/iot_security` | Protection of IoT devices and networks |
| `technology/iot/smart_homes` | Residential IoT environments |
| **networking** | |
| `technology/networking/networking` | Computer network design and management |
| `technology/networking/network_architecture` | Network topology, protocols, and components |
| `technology/networking/network_management` | Monitoring, configuring, and optimizing networks |
| `technology/networking/network_operations` | Smooth operation of network infrastructure |
| `technology/networking/network_protocols` | Rules governing device communication |
| `technology/networking/network_security` | Protection from unauthorized access |
| **security** | |
| `technology/security/security` | Protecting systems from cyber threats |
| `technology/security/application_security` | Protecting applications from threats |
| `technology/security/cyber_network_security` | Network protection from attacks |
| `technology/security/cybersecurity` | Protection from digital attacks |
| `technology/security/data_security` | Digital data protection throughout lifecycle |
| `technology/security/identity_management` | Managing digital identities and access |
| `technology/security/incident_management` | Detecting and resolving security incidents |
| **software_engineering** | |
| `technology/software_engineering/software_engineering` | Software design, development, and maintenance |
| `technology/software_engineering/apis_integration` | APIs and integration technologies |
| `technology/software_engineering/devops` | Development + operations practices |
| `technology/software_engineering/mlops` | ML + DevOps lifecycle management |
| `technology/software_engineering/quality_assurance` | Testing, code review, quality standards |
| `technology/software_engineering/software_development` | Designing, creating, testing software |

### telecommunications

| Slug | Description |
|------|-------------|
| `telecommunications/telecommunications` | (category root) |
| `telecommunications/internet_services` | ISP operations, broadband, connectivity |
| `telecommunications/iot_connectivity` | IoT networks, M2M, NB-IoT, LoRaWAN |
| `telecommunications/network_infrastructure` | Fiber optics, network equipment |
| `telecommunications/telecom_operations` | Service provisioning, billing, customer management |
| `telecommunications/voip_and_unified_communications` | VoIP, video conferencing, collaboration |
| `telecommunications/wireless_communications` | Mobile networks, 5G/6G, cellular services |

### transportation

| Slug | Description |
|------|-------------|
| `transportation/transportation` | (category root) |
| `transportation/automotive` | Vehicle design, engineering, manufacturing |
| `transportation/autonomous_vehicles` | Self-driving technology and vehicle AI |
| `transportation/freight` | Freight forwarding, cargo management |
| `transportation/logistics` | Warehousing, distribution, transportation planning |
| `transportation/public_transit` | Urban transit, rail, bus networks |
| `transportation/supply_chain` | Production, processing, distribution of goods |

### trust_and_safety

| Slug | Description |
|------|-------------|
| `trust_and_safety/trust_and_safety` | (category root) |
| `trust_and_safety/content_moderation` | Reviewing user content against guidelines |
| `trust_and_safety/data_privacy` | Personal information protection and compliance |
| `trust_and_safety/fraud_prevention` | Identifying and stopping fraudulent activities |
| `trust_and_safety/online_safety` | Protecting internet users from harm |
| `trust_and_safety/risk_management` | Identifying, assessing, and prioritizing risks |
