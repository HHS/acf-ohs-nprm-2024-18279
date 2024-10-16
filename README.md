[![LICENSE](https://img.shields.io/badge/Link-License-blue.svg)](https://github.com/HHS/acf-ohs-nprm-2024-18279/blob/main/LICENSE)

[![DISCLAIMER](https://img.shields.io/badge/Link-Disclaimer-blue.svg)](https://github.com/HHS/acf-ohs-nprm-2024-18279/blob/main/DISCLAIMER)

# acf-ohs-nprm-2024-18279
Analysis of public comments received on proposed rule on Supporting the Head Start Workforce and Consistent Quality Programming
- [Notice of Proposed Rulemaking, Nov-2023](https://www.federalregister.gov/documents/2023/11/20/2023-25038/supporting-the-head-start-workforce-and-consistent-quality-programming)
- [Final Rule, Aug-2024](https://www.federalregister.gov/documents/2024/08/21/2024-18279/supporting-the-head-start-workforce-and-consistent-quality-programming)

This purpose of open-sourcing this repository is to be transparent about how AI was used to assist in efficiently analyzing public comments and to provide a starting point for others who would like to explore using commercial Large Language Models to aide in the public comment analysis process.

## Links to Project Documentation:
[How to Run](documentation/how_to_run.md): Outlines how to replicate the project and run the files in this repo.\
[Technical Documentation](documentation/full_technical_documentation.md): Full technical documentation for this project including technical considerations for future project iterations and the rationale behind some of our choices.\
[Cloud Architecture](documentation/cloud_architecture.md): A detailed outline of how we structured our cloud infrastructure.\
[Lessons Learned](documentation/lessons_learned.md): A collection of lessons learned from the Policy Team and the Data Surge Team.
  
## Folder explanation:
inputs/: Should hold pickle file and file used for bill tagging

json_outputs/: Holds one output for each chunk of text that's sent to chatGPT with a prompt. 

logs/: Log files will be created when you run data_processing.py and gpt_parallel.py. Logs are timestamped and indicate if there were any issues with particular comments when sending to chatGPT, and the time it takes to run both scripts.

outputs/: Holds an "intermediate" and "final" folder. "Intermediate" folder holds the chunked pickle file created in part of the pipeline. "Final" holds the final csvs exported in long and wide formats as well as the failed_jsons_files.csv and the summaries documents
