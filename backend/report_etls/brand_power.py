import json
import logging
from string import Template
from typing import List
from dataclasses import dataclass

from abstractions.EtlReportBase import EtlReportBase
from abstractions.ILLMServiceManager import ILLMServiceManager
from models.request.LLMRequestResourceModel import LLMRequestResourceModel
from utility.Utility import Utility

'''
TODO:
List competitors -> get source scores -> generate zerveme scores for each
company -> generate report
'''

EXAMPLE_STRUCTURE_FOR_COMPETITOR_LIST = """
[
  {
    "rank": 1,
    "name": "SingleStore",
    "traits": ["High-performance", "Low-latency"],
    "description": "SingleStore delivers industry-leading throughput and "
                   "sub-second analytics on HTAP workloads with unified "
                   "SQL engine and vector acceleration.",
    "sources": [
      "https://www.singlestore.com/blog/singlestore-kai-real-time-analytics-benchmarks/",
      "https://www.singlestore.com/blog/tpc-benchmarking-results/",
      "https://venturebeat.com/data-infrastructure/singlestoredb-8-9-update-unifies-ai-and-real-time-analytics/",
      "https://www.businesswire.com/news/home/20220615005393/en/SingleStore-Outshines-Major-Database-Competitors-in-TCO-Study",
      "https://blog.min.io/building-next-gen-data-solutions-singlestore-minio-and-the-modern-datalake-stack/"
    ]
  },
  {
    "rank": 2,
    "name": "CockroachDB",
    "traits": ["Resilient", "Scalable"],
    "description": "CockroachDB automatically handles node failures and "
                   "network partitions while scaling horizontally across "
                   "regions for global consistency.",
    "sources": [
      "https://www.cockroachlabs.com/blog/stress-testing-cockroachdb-resilience/",
      "https://dotcommagazine.com/2024/03/cockroachdb-a-fascinating-comprehensive-guide/",
      "https://thenewstack.io/how-cockroachdb-reimagines-database-resilience/",
      "https://en.wikipedia.org/wiki/Distributed_SQL",
      "https://www.reddit.com/r/kubernetes/comments/1dgx0yn"
    ]
  },
  {
    "rank": 3,
    "name": "Snowflake",
    "traits": ["Cloud-based", "Scalable"],
    "description": "Snowflake's decoupled storage and compute "
                   "architecture enables elastic scaling and "
                   "multi-cloud analytics without infrastructure "
                   "constraints.",
    "sources": [
      "https://technologymagazine.com/articles/snowflake-a-transformative-force-in-data-and-analytics",
      "https://builtin.com/data-science/snowflake-cloud-data-platform",
      "https://integrate.io/blog/snowflake-data-transformation/",
      "https://topbusinesssoftware.com/categories/distributed-databases/",
      "https://data-sleek.com/singlestore-vs-clickhouse-benchmarks/"
    ]
  },
  {
    "rank": 4,
    "name": "PostgreSQL",
    "traits": ["Reliable", "Open-source"],
    "description": "PostgreSQL is a mature, extensible open-source "
                   "RDBMS praised for its reliability and strong SQL "
                   "feature set across diverse workloads.",
    "sources": [
      "https://www.g2.com/products/singlestore-singlestore/competitors/alternatives",
      "https://www.postgresql.org/about/",
      "https://blog.min.io/building-next-gen-data-solutions-singlestore-minio-and-the-modern-datalake-stack/",
      "https://topbusinesssoftware.com/categories/distributed-databases/",
      "https://www.reddit.com/r/dataengineering/comments/1epl3j7"
    ]
  },
  {
    "rank": 5,
    "name": "MySQL",
    "traits": ["User-friendly", "Cost-effective"],
    "description": "MySQL is widely adopted, easy to administer, and "
                   "cost-efficient for web and application workloads, "
                   "though lacking built-in HTAP support.",
    "sources": [
      "https://www.g2.com/products/singlestore-singlestore/competitors/alternatives",
      "https://www.capterra.com/p/143032/MemSQL/alternatives/",
      "https://topbusinesssoftware.com/categories/distributed-databases/",
      "https://blog.min.io/building-next-gen-data-solutions-singlestore-minio-and-the-modern-datalake-stack/",
      "https://data-sleek.com/singlestore-vs-clickhouse-benchmarks/"
    ]
  },
  {
    "rank": 6,
    "name": "Amazon Aurora",
    "traits": ["Scalable", "Reliable"],
    "description": "Aurora offers MySQL/PostgreSQL compatibility with "
                   "high availability and auto-scaling in AWS-managed "
                   "infrastructure, optimizing performance at scale.",
    "sources": [
      "https://www.g2.com/products/singlestore-singlestore/competitors/alternatives",
      "https://www.businesswire.com/news/home/20220615005393/en/SingleStore-Outshines-Major-Database-Competitors-in-TCO-Study",
      "https://topbusinesssoftware.com/categories/distributed-databases/",
      "https://blog.min.io/building-next-gen-data-solutions-singlestore-minio-and-the-modern-datalake-stack/",
      "https://www.reddit.com/r/dataengineering/comments/1epl3j7"
    ]
  },
  {
    "rank": 7,
    "name": "IBM Db2",
    "traits": ["Reliable", "Secure"],
    "description": "Db2 is an enterprise-grade RDBMS known for robust "
                   "transactional performance, high security standards, "
                   "and enterprise scalability.",
    "sources": [
      "https://www.g2.com/products/singlestore-singlestore/competitors/alternatives",
      "https://topbusinesssoftware.com/categories/distributed-databases/",
      "https://en.wikipedia.org/wiki/NuoDB",
      "https://www.businesswire.com/news/home/20220615005393/en/SingleStore-Outshines-Major-Database-Competitors-in-TCO-Study",
      "https://blog.min.io/building-next-gen-data-solutions-singlestore-minio-and-the-modern-datalake-stack/"
    ]
  },
  {
    "rank": 8,
    "name": "Google Cloud SQL",
    "traits": ["User-friendly", "Cloud-based"],
    "description": "Cloud SQL is a fully managed relational service "
                   "on Google Cloud offering ease-of-use, automated "
                   "maintenance, and cloud-native scalability.",
    "sources": [
      "https://www.g2.com/products/singlestore-singlestore/competitors/alternatives",
      "https://topbusinesssoftware.com/categories/distributed-databases/",
      "https://blog.min.io/building-next-gen-data-solutions-singlestore-minio-and-the-modern-datalake-stack/",
      "https://data-sleek.com/singlestore-vs-clickhouse-benchmarks/",
      "https://builtin.com/data-science/snowflake-cloud-data-platform"
    ]
  },
  {
    "rank": 9,
    "name": "SAP HANA Cloud",
    "traits": ["High-performance", "Cloud-based"],
    "description": "SAP HANA Cloud processes in-memory analytics and "
                   "transactional workloads at scale with optimized "
                   "performance in a cloud-native environment.",
    "sources": [
      "https://www.g2.com/products/singlestore-singlestore/competitors/alternatives",
      "https://topbusinesssoftware.com/categories/distributed-databases/",
      "https://canvasbusinessmodel.com/blogs/competitors/singlestore-competitive-landscape",
      "https://data-sleek.com/singlestore-vs-clickhouse-benchmarks/",
      "https://venturebeat.com/data-infrastructure/singlestoredb-8-9-update-unifies-ai-and-real-time-analytics/"
    ]
  },
  {
    "rank": 10,
    "name": "Snowflake",
    "traits": ["Analytical-optimized", "Scalable"],
    "description": "Snowflake dominates for large-scale analytics "
                   "workloads due to its elastic scalability, "
                   "multi-cloud support, and separation of compute "
                   "and storage.",
    "sources": [
      "https://technologymagazine.com/articles/snowflake-a-transformative-force-in-data-and-analytics",
      "https://builtin.com/data-science/snowflake-cloud-data-platform",
      "https://integrate.io/blog/snowflake-data-transformation/",
      "https://topbusinesssoftware.com/categories/distributed-databases/",
      "https://data-sleek.com/singlestore-vs-clickhouse-benchmarks/"
    ]
  }
]
"""

LIST_COMPETITORS_BASE_PROMPT = Template(
    "Please list top 10 competitors for the company `$company_name` "
    "and website `$company_website` in the `$industries` industries, "
    "in location `$location`. Short description of this company is "
    "`$description`. Known competitors are `$competitors`."
)

FORMAT_INSTRUCTIONS = Template(
    "Please output a JSON list of the top 10 competitors for the "
    "company, ranked from 1 to 10.\n\n"
    "Please include our target company\n\n"
    "Each competitor must have the following fields:\n\n"
    "- `rank`: Integer from 1 to 10\n"
    "- `name`: Name of the company\n, if our target company "
    "please use the input format"
    "- `traits`: List of the top 2 traits, chosen from this "
    "mapping: $industry_traits_mapping\n"
    "- `description`: A short 1-2 sentence description "
    "explaining why they are a competitor\n"
    "- `discoverability`: Integer from 1 to 10 indicating how "
    "easy it is to discover this competitor\n"
    "- `sources`: A list of at least 5 distinct links to blogs, "
    "news, or other credible sources that justify the traits or "
    "relevance of the competitor\n\n"
    "Use real, specific links wherever possible (not generic "
    "homepages)."
    "If you are not able to locate the company, please return an "
    "empty JSON. DO NOT ASSUME, IF TARGET COMPANY DOES NOT EXIST "
    "PLEASE DO NOT GUESS\n\n"
)

SOURCE_RANKING_PROMPT = Template("""
Please provide a detailed list of $industry news websites and blogs
that are top sources for $industry industry information. For each
source, include:

- `name`: The name of the website or blog
- `score`: A popularity rating from 1 to 10, where 10 means highest
popularity/user count and 1 means low popularity
- `focus`: A brief description of the primary focus or specialty of the
source (e.g., AI news, consumer tech, marketing tech)
- `url`: The direct URL to the source's homepage or main technology
section

Please rank the list roughly by popularity and influence in the
$industry space, covering a mix of general tech, AI, marketing tech,
and niche sites. Include at least 15 entries.

Format the output as a JSON array of objects, for example:

[
  {
    "name": "TechCrunch",
    "score": 10,
    "focus": "Startup and tech news",
    "url": "https://techcrunch.com"
  },
  ...
]
""")

TASK_SYS_PROMPT = ("You are an expert in market analysis and "
                   "competitor identification.")


@dataclass
class CompanyDataResponse:
    name: str
    competitors: List[dict]
    sources_from_pull: List[dict]

    def to_dict(self):
        """Convert CompanyDataResponse to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'competitors': self.competitors,
            'sources_from_pull': self.sources_from_pull
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Convert cached dictionary data back to CompanyDataResponse"""
        return cls(
            name=data.get('name', ''),
            competitors=data.get('competitors', []),
            sources_from_pull=data.get('sources_from_pull', [])
        )


class BrandPower(EtlReportBase):
    EXPECTED_RUN_PARAMS_FIELDS = [
        "target_industries",
        "company_name",
        "description_of_company",
        "company_website",
        "location",
        "known_competitors"
    ]

    def __init__(self, run_params: dict,
                 llm_service_manager: ILLMServiceManager,
                 db_service=None):
        super().__init__(run_params, "brand_power", llm_service_manager, db_service)

        self.__industries = Utility.read_in_json_file(
            "report_etls/report_resources/brand_power_resources/"
            "industries.json"
        )

        self.__top_industry_sources = Utility.read_in_json_file(
            "report_etls/report_resources/brand_power_resources/"
            "top_industry_sources.json"
        )

    def configure_init_tasks(self):
        self._pre_validation_pipeline_tasks = {
            "Check run params": self.__check_run_params
        }
        self._extract_pipeline_tasks = {
            "Get prompt data from LLM": self.__get_llm_data_for_report
        }
        self._transform_process_pipeline_tasks = {
            "Transform and generate report": self.__transform_and_generate_report
        }

    def __check_run_params(self):
        missing_fields = (set(self.EXPECTED_RUN_PARAMS_FIELDS) -
                          set(self._run_params.keys()))
        if missing_fields:
            raise ValueError(
                f"Missing required run parameters: "
                f"{', '.join(missing_fields)}"
            )

        for field in self.EXPECTED_RUN_PARAMS_FIELDS:
            if not self._run_params.get(field):
                raise ValueError(
                    f"Run parameter '{field}' cannot be empty."
                )

        target_industries = self._run_params.get("target_industries", [])
        if not target_industries:
            raise ValueError("Target industries cannot be empty.")

        if not all(
            industry.lower() in (i.lower() for i in self.__industries)
            for industry in target_industries
        ):
            raise ValueError("Invalid target industries specified.")

        logging.info("Run parameters validated successfully.")

    # TODO add more test cases for this
    def __get_list_competitors_prompt(self, **param_overrides):

        # if param_overrides is provided, use it to override the run_params
        if param_overrides:
            self._run_params.update(param_overrides)

        company_name = self._run_params.get("company_name")
        company_website = self._run_params.get("company_website")
        industries = self._run_params.get("target_industries", [])
        location = self._run_params.get("location")
        description = self._run_params.get("description_of_company", "")
        competitors = self._run_params.get("known_competitors", [])

        return LIST_COMPETITORS_BASE_PROMPT.substitute(
            company_name=company_name,
            company_website=company_website,
            industries=",".join(industries),
            location=location,
            description=description,
            competitors=",".join(competitors)
        )

    def __generate_base_prompts(self, **param_overrides):
        logging.info("Crafting prompts...")

        list_competitors_prompt = self.__get_list_competitors_prompt(
            **param_overrides
        )
        industry_traits_mapping = self.__industries

        format_instructions = FORMAT_INSTRUCTIONS.substitute(
            industry_traits_mapping=json.dumps(
                industry_traits_mapping, indent=2
            )
        )

        full_prompt = f"{list_competitors_prompt}\n\n{format_instructions}"

        industry_list = (self._run_params.get("target_industries") or
                         ["technology"])
        industry = industry_list[0]

        return {
            'list_competitors': {
                "system": TASK_SYS_PROMPT,
                "user": full_prompt
            },
            'source_ranking': {
                "system": TASK_SYS_PROMPT,
                "user": SOURCE_RANKING_PROMPT.substitute(
                    industry=industry
                )
            }
        }

    def __get_llm_data_for_report(self):
        # Load cache first - if cache exists, use it entirely
        if self.load_cache():
            logging.info("Using cached LLM response data")
            self._convert_cached_data_to_objects()
            return

        # No cache found, proceed with LLM calls
        # call this __generate_base_prompts here to get company specific
        # info dynamically
        target_company_prompt_data = self.__generate_base_prompts()
        logging.info("Generated prompts for target company.")
        target_company_response = self.__send_prompts_to_llm(
            prompt_data=target_company_prompt_data['list_competitors'],
            source_ranking_prompt=target_company_prompt_data[
                'source_ranking'
            ]
        )

        if not target_company_response.competitors:
            logging.warning("No competitors found for the target company.")
            return

        competitors = [
            company['name'] for company in target_company_response.competitors
            if company['name'].lower() != target_company_response.name.lower()
        ]

        # store the target company data
        self._llm_response_data["target_company"] = {
            target_company_response.name: {
                    "company_data_response": target_company_response
                }
        }

        self._llm_response_data["competitors"] = {}

        comp_count = len(competitors)
        i = 1
        for comp in competitors:
            logging.info(f"Processing competitor: {comp}... ({i}/{comp_count})")
            prompt_data = self.__generate_base_prompts(company_name=comp)
            response_data = self.__send_prompts_to_llm(
                prompt_data=prompt_data['list_competitors'],
                source_ranking_prompt=prompt_data['source_ranking']
            )

            # Always store response
            self._llm_response_data["competitors"][response_data.name] = {
                "company_data_response": response_data
            }

            i += 1

        # Always save cache
        self.save_cache()

    def _convert_cached_data_to_objects(self):
        """Convert cached dictionary data back to CompanyDataResponse objects"""
        if "target_company" in self._llm_response_data:
            for company_name, company_data in self._llm_response_data["target_company"].items():
                if isinstance(company_data["company_data_response"], dict):
                    self._llm_response_data["target_company"][company_name]["company_data_response"] = \
                        CompanyDataResponse.from_dict(company_data["company_data_response"])

        if "competitors" in self._llm_response_data:
            for company_name, company_data in self._llm_response_data["competitors"].items():
                if isinstance(company_data["company_data_response"], dict):
                    self._llm_response_data["competitors"][company_name]["company_data_response"] = \
                        CompanyDataResponse.from_dict(company_data["company_data_response"])

    def __send_prompts_to_llm(self, prompt_data, source_ranking_prompt):
        logging.info("Sending prompts to LLM...")

        # send list competitors prompt, then use that to get the source
        # ranking
        comp_prompt_request = LLMRequestResourceModel(
            prompt=prompt_data['user'],
            system_prompt=prompt_data['system'],
            examples=EXAMPLE_STRUCTURE_FOR_COMPETITOR_LIST,
            response_type="dict"
        )

        comp_llm_response = self._llm_service_manager.run_task(
            comp_prompt_request
        )
        logging.info("List competitors response received.")
        logging.debug(
            f"List competitors response: "
            f"{comp_llm_response.response_content}"
        )
        # send source ranking prompt
        source_ranking_request = LLMRequestResourceModel(
            prompt=source_ranking_prompt['user'],
            system_prompt=TASK_SYS_PROMPT,
            response_type="dict",
            history_messages=comp_llm_response.history_messages
        )

        source_ranking_response = self._llm_service_manager.run_task(
            source_ranking_request
        )
        logging.info("Source ranking response received.")
        logging.debug(
            f"Source ranking response: "
            f"{source_ranking_response.response_content}"
        )

        return CompanyDataResponse(
            name=self._run_params.get("company_name"),
            competitors=list(comp_llm_response.response_content.values())[0]
                if comp_llm_response.response_content else [],
            sources_from_pull=list(source_ranking_response.response_content.values())[0]
                if source_ranking_response.response_content else []
        )

    # TODO implement this
    def __transform_and_generate_report(self):
        if not self._llm_response_data:
            logging.error("No LLM response data available to transform.")
            return

        logging.info("Transforming and generating report...")

        target_company_data = self._llm_response_data.get("target_company", {})
        competitors_data = self._llm_response_data.get("competitors", {})

        if not target_company_data:
            logging.error("No target company data found.")
            return
        if not competitors_data:
            # not necessarily an error, could be no competitors found -- we should handle this
            logging.error("No competitors data found.")
            return

        # a lot going on, and potentials

        # calculate the score for target company
        # include recommendations on how to improve the score (sources missing?)

        # get ranked sources df we can display as well

        # calculate the score of each competitor

        # feed llm --> llm can generate a summary report for us [optional bonus]

        # save data as DF

        # store in db

        # return response for API
