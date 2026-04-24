#!/usr/bin/env python3
"""
Enhanced Protein Design & Bioinformatics Competition Aggregator
Wider coverage, better metadata extraction, more interactive UI
"""

import feedparser
import datetime
import json
import os
import re
import requests
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Tuple

DB_FILE = "competitions_db.json"

# ═══════════════════════════════════════════════════════════════════════════════
# MASSIVELY EXPANDED KEYWORD NET
# ═══════════════════════════════════════════════════════════════════════════════

KEYWORDS = [
    # Core science
    'protein', 'proteomics', 'peptide', 'amino acid', 'enzyme', 'antibody',
    'antigen', 'epitope', 'nanobody', 'aptamer', 'bispecific', 'therapeutic',
    'cytokine', 'hormone', 'receptor', 'signaling', 'pathway', 'metabolism',
    
    # Design / modelling
    'binder', 'ligand', 'docking', 'alphafold', 'rosetta', 'esmfold',
    'protein design', 'protein engineering', 'de novo', 'directed evolution',
    'structure prediction', 'function prediction', 'molecular dynamics',
    'folding', 'unfolding', 'aggregation', 'amyloid', 'prion', 'chaperone',
    'thermodynamics', 'kinetics', 'biophysics', 'structural bioinformatics',
    
    # Synthetic / systems biology
    'synthetic biology', 'igem', 'metabolic engineering', 'gene circuit',
    'bioparts', 'biobrick', 'chassis', 'biosensor', 'bioreactor', 'biomaterial',
    'biofuel', 'bioremediation', 'genetic circuit', 'promoter', 'terminator',
    'plasmid', 'vector', 'cloning', 'assembly', 'golden gate', 'gibson',
    
    # Drug / biotech
    'drug discovery', 'drug design', 'hit identification', 'lead optimisation',
    'ADMET', 'pharmacophore', 'virtual screening', 'QSAR', 'molecular docking',
    'fragment screening', 'high-throughput screening', 'assay development',
    'medicinal chemistry', 'pharmacology', 'toxicology', 'formulation',
    'biopharma', 'biotech', 'pharma', 'therapeutics', 'vaccine', 'immunotherapy',
    'cell therapy', 'gene therapy', 'CRISPR', 'gene editing', 'car-t',
    
    # Structural biology
    'structural biology', 'cryo-em', 'cryo em', 'nmr structure', 'x-ray crystallography',
    'pdb', 'protein data bank', 'fold', 'domain', 'motif', 'secondary structure',
    'alpha helix', 'beta sheet', 'loop', 'coil', 'disorder', 'intrinsically disordered',
    'post-translational modification', 'glycosylation', 'phosphorylation',
    
    # ML / AI in biology
    'machine learning protein', 'deep learning biology', 'generative biology',
    'diffusion model protein', 'language model protein', 'geometric deep learning',
    'graph neural network biology', 'transformer', 'attention', 'embedding',
    'representation learning', 'transfer learning', 'few-shot learning',
    'bioinformatics', 'computational biology', 'systems biology', 'network biology',
    
    # Omics
    'genomics', 'proteomics', 'transcriptomics', 'metabolomics', 'lipidomics',
    'glycomics', 'multiomics', 'single cell', 'spatial omics', 'mass spec',
    'sequencing', 'NGS', 'microarray', 'HPLC', 'chromatography', 'spectroscopy',
    
    # Competition signals
    'hackathon', 'competition', 'challenge', 'contest', 'prize', 'award',
    'grant', 'fellowship', 'kaggle', 'CASP', 'CAMEO', 'CAFA', 'CAMDA', 'CAGI',
    'biomolecular', 'bioinformatics challenge', 'data challenge', 'benchmark',
    'shared task', 'evaluation', 'assessment', 'blind prediction',
    
    # Funding & career
    'scholarship', 'stipend', 'travel grant', 'conference grant', 'research grant',
    'early career', 'phd', 'postdoc', 'young investigator', 'student',
    'training', 'workshop', 'summer school', 'winter school', 'course',
]

# ═══════════════════════════════════════════════════════════════════════════════
# EXPANDED RSS / FEED SOURCES
# ═══════════════════════════════════════════════════════════════════════════════

RSS_SOURCES = {
    # Core Scientific Journals
    "Nature Proteomics":          "https://www.nature.com/subjects/proteomics.rss",
    "Nature Structural & Mol Bio":"https://www.nature.com/subjects/structural-biology.rss",
    "Nature Biotechnology":       "https://www.nature.com/nbt.rss",
    "Nature Methods":             "https://www.nature.com/nmeth.rss",
    "Nature Computational Sci":   "https://www.nature.com/natcomputsci.rss",
    "PLOS Computational Biology": "https://journals.plos.org/ploscompbiol/feed/atom",
    "PLOS Biology":               "https://journals.plos.org/plosbiology/feed/atom",
    "Bioinformatics (Oxford)":    "https://academic.oup.com/rss/site_6101/3186.xml",
    "BMC Bioinformatics":         "https://bmcbioinformatics.biomedcentral.com/articles/most-recent/rss.xml",
    "NAR (Nucleic Acids Res)":    "https://academic.oup.com/rss/site_6101/3188.xml",
    "Structure (Cell)":          "https://www.cell.com/structure/rss/current",
    "Protein Science":            "https://onlinelibrary.wiley.com/feed/1469896x/most-recent",
    "Proteins: Struct Func Bioinf": "https://onlinelibrary.wiley.com/feed/10970134/most-recent",
    
    # Preprints
    "bioRxiv (Bioinformatics)":   "https://biorxiv.org/rss/category/bioinformatics",
    "bioRxiv (Biochemistry)":     "https://biorxiv.org/rss/category/biochemistry",
    "bioRxiv (Biophysics)":     "https://biorxiv.org/rss/category/biophysics",
    "bioRxiv (Systems Biology)": "https://biorxiv.org/rss/category/systems-biology",
    "bioRxiv (Synthetic Biology)": "https://biorxiv.org/rss/category/synthetic-biology",
    "bioRxiv (Computational Biology)": "https://biorxiv.org/rss/category/computational-biology",
    "medRxiv (Bioinformatics)":   "https://medrxiv.org/rss/category/bioinformatics",
    "arXiv (Quantitative Biology)": "http://export.arxiv.org/rss/q-bio",
    "arXiv (Bioinformatics)":   "http://export.arxiv.org/rss/q-bio.BM",
    "arXiv (Biomolecules)":      "http://export.arxiv.org/rss/q-bio.BM",
    
    # Industry & Company Blogs
    "Adaptyv Bio (Substack)":     "https://adaptyvbio.substack.com/feed",
    "Oxford BLOPIG":              "https://blopig.com/blog/feed/",
    "DeepMind Blog":              "https://deepmind.google/blog/rss.xml",
    "OpenAI Research":            "https://openai.com/research/rss.xml",
    "Microsoft Research (Bio)":   "https://www.microsoft.com/en-us/research/research-area/biological-sciences/rss/",
    "Recursion (Decode Blog)":    "https://www.recursion.com/blog/rss.xml",
    "Relay Therapeutics":         "https://relaytx.com/newsroom/feed",
    "Generate Biomedicines":      "https://generatebiomedicines.com/news/feed",
    "Chroma Medicine":            "https://chroma.bio/news/feed",
    "Dyno Therapeutics":          "https://dynotx.com/news/feed",
    "Strateos Blog":              "https://strateos.com/blog/feed",
    "Benchling Blog":             "https://www.benchling.com/blog/feed",
    "Tessera Therapeutics":       "https://tesseratherapeutics.com/news/feed",
    
    # Infrastructure & Tools
    "OpenTargets Blog":           "https://blog.opentargets.org/rss/",
    "EMBL-EBI News":              "https://www.ebi.ac.uk/about/news/feed/",
    "PDB (RCSB News)":            "https://www.rcsb.org/news/rss",
    "AlphaFold Server Updates":   "https://alphafoldserver.com/feed",
    "UniProt News":               "https://www.uniprot.org/rss/news.xml",
    "PDB-Dev News":               "https://pdb-dev.wwpdb.org/feed",
    "ChemRxiv":                   "https://chemrxiv.org/eng/rss/feed",
    "Zotero Bioinformatics":      "https://www.zotero.org/groups/23877/bioinformatics/items.rss",
    
    # Competition Platforms
    "Kaggle Competitions":        "https://www.kaggle.com/competitions.rss",
    "Kaggle Datasets":            "https://www.kaggle.com/datasets.rss",
    "DrivenData Competitions":    "https://www.drivendata.org/competitions.rss",
    "CodaLab Competitions":       "https://codalab.org/feed",
    "CodaLab Worksheets":         "https://worksheets.codalab.org/feed",
    "AIcrowd Challenges":         "https://www.aicrowd.com/challenges.rss",
    "DataDriven (Challenges)":    "https://www.datadrivencompetition.com/feed",
    "Grand Challenges (NIH)":     "https://www.grandchallenges.org/feed",
    
    # Synthetic Biology
    "Synbiobeta":                 "https://synbiobeta.com/feed/",
    "iGEM Foundation":            "https://igem.org/feed",
    "Addgene Blog":               "https://blog.addgene.org/rss",
    "Twist Bioscience":           "https://www.twistbioscience.com/news/feed",
    "Ginkgo Bioworks":            "https://www.ginkgobioworks.com/news/feed",
    "Synthetic Genomics":         "https://www.syntheticgenomics.com/news/feed",
    
    # Academic Institutions & Conferences
    "MIT CSAIL (Bio)":          "https://www.csail.mit.edu/research/biological-engineering/rss",
    "Stanford Bioengineering":    "https://bioengineering.stanford.edu/news/feed",
    "Harvard Systems Biology":    "https://sysbio.med.harvard.edu/news/feed",
    "Broad Institute":            "https://www.broadinstitute.org/news/rss",
    "Scripps Research":           "https://www.scripps.edu/news/feed",
    "EMBL News":                  "https://www.embl.org/news/feed/",
    "Max Planck Institute":       "https://www.mpg.de/en/news/rss",
    "Cold Spring Harbor":         "https://www.cshl.edu/news/feed/",
    "Wellcome Trust":             "https://wellcome.org/news/feed",
    "ISCB (Int Soc Comp Bio)":    "https://www.iscb.org/rss",
    "PSB (Pacific Symposium)":    "https://psb.stanford.edu/rss",
    "ISMB/ECCB":                  "https://www.iscb.org/ismbeccb/rss",
    "RECOMB":                     "https://recomb.org/rss",
    "ECCB":                       "https://eccb.eu/rss",
    
    # Funding & Grants
    "NIH Funding News":           "https://www.nih.gov/research-training/medical-research-initiatives/rss",
    "NSF Biology News":           "https://www.nsf.gov/rss/bio.xml",
    "NSF CISE (Comp Sci)":        "https://www.nsf.gov/rss/cise.xml",
    "ERC (Europe) News":          "https://erc.europa.eu/news/rss",
    "Horizon Europe":             "https://research-and-innovation.ec.europa.eu/news/feed_en",
    "BBSRC (UK) News":            "https://www.ukri.org/news/feed",
    "Wellcome Funding":           "https://wellcome.org/grant-funding/feed",
    "Gates Foundation":           "https://www.gatesfoundation.org/ideas/rss",
    "Chan Zuckerberg Initiative": "https://chanzuckerberg.com/news/feed/",
    "HHMI News":                  "https://www.hhmi.org/news/rss",
    "Human Frontier Sci Program":   "https://www.hfsp.org/news/feed",
    "EMBO Fellowships":           "https://www.embo.org/news/feed",
    
    # Tech Platforms
    "Google AI Blog":             "https://ai.googleblog.com/feeds/posts/default",
    "Meta AI Research":           "https://ai.meta.com/blog/rss/",
    "NVIDIA AI Blog":             "https://blogs.nvidia.com/ai/feed",
    "AWS ML Blog":                "https://aws.amazon.com/blogs/machine-learning/feed/",
    "Azure AI Blog":              "https://azure.microsoft.com/en-us/blog/topics/ai/feed/",
    
    # Specialized Forums
    "Reddit r/bioinformatics":    "https://www.reddit.com/r/bioinformatics.rss",
    "Reddit r/comp_chem":         "https://www.reddit.com/r/comp_chem.rss",
    "Hacker News (Bio)":          "https://hnrss.org/newest?q=protein+bioinformatics",
    "F6S (Startup Competitions)":   "https://www.f6s.com/company/feed",
    "Devpost Hackathons":         "https://devpost.com/feed",
}

# ═══════════════════════════════════════════════════════════════════════════════
# DEDICATED SCRAPERS FOR COMPETITION-SPECIFIC SITES
# ═══════════════════════════════════════════════════════════════════════════════

SCRAPE_TARGETS = {
    "Proteinbase / Adaptyv": {
        "url": "https://proteinbase.com/competitions",
        "link_pattern": "/competitions/",
        "base": "https://proteinbase.com",
        "organizer": "Adaptyv Bio",
        "location": "Remote (wet-lab validation provided)",
        "prizes": "Wet-lab validation + Cash",
    },
    "CASP (Critical Assessment)": {
        "url": "https://predictioncenter.org",
        "link_pattern": "/casp",
        "base": "https://predictioncenter.org",
        "organizer": "CASP / UC San Diego",
        "location": "Global – Remote submissions",
        "prizes": "Recognition + Conference Invitation",
    },
    "CAMEO (Continuous)": {
        "url": "https://www.cameo3d.org",
        "link_pattern": "/",
        "base": "https://www.cameo3d.org",
        "organizer": "SIB Swiss Institute of Bioinformatics",
        "location": "Remote",
        "prizes": "Continuous benchmarking",
    },
    "CAFA (Critical Assessment)": {
        "url": "https://cafa.iddo.org",
        "link_pattern": "/",
        "base": "https://cafa.iddo.org",
        "organizer": "CAFA Consortium",
        "location": "Remote",
        "prizes": "Publication + ISMB invitation",
    },
    "DREAM Challenges": {
        "url": "https://dreamchallenges.org",
        "link_pattern": "/challenge/",
        "base": "https://dreamchallenges.org",
        "organizer": "Sage Bionetworks",
        "location": "Remote",
        "prizes": "Co-authorship + Recognition",
    },
    "Kaggle (Bio Competitions)": {
        "url": "https://www.kaggle.com/competitions",
        "link_pattern": "/competitions/",
        "base": "https://www.kaggle.com",
        "organizer": "Kaggle / Various",
        "location": "Online",
        "prizes": "Cash prizes",
    },
    "AIcrowd (Challenges)": {
        "url": "https://www.aicrowd.com/challenges",
        "link_pattern": "/challenges/",
        "base": "https://www.aicrowd.com",
        "organizer": "AIcrowd / Various",
        "location": "Online",
        "prizes": "Varies by challenge",
    },
    "DrivenData": {
        "url": "https://www.drivendata.org/competitions/",
        "link_pattern": "/competitions/",
        "base": "https://www.drivendata.org",
        "organizer": "DrivenData",
        "location": "Online",
        "prizes": "Prizes + Social impact",
    },
    "iGEM Competition": {
        "url": "https://competition.igem.org",
        "link_pattern": "/",
        "base": "https://competition.igem.org",
        "organizer": "iGEM Foundation",
        "location": "Paris, France",
        "prizes": "Medals + Special awards",
    },
    "CodaLab": {
        "url": "https://codalab.org/competitions",
        "link_pattern": "/competitions/",
        "base": "https://codalab.org",
        "organizer": "CodaLab",
        "location": "Online",
        "prizes": "Varies",
    },
    "Grand Challenges (NIH)": {
        "url": "https://www.grandchallenges.org/challenges",
        "link_pattern": "/challenges/",
        "base": "https://www.grandchallenges.org",
        "organizer": "NIH",
        "location": "USA",
        "prizes": "Grants + Funding",
    },
    "Ensembl Blog": {
        "url": "https://www.ensembl.info",
        "link_pattern": "/",
        "base": "https://www.ensembl.info",
        "organizer": "EMBL-EBI",
        "location": "Remote",
        "prizes": "N/A",
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# EXPANDED SEED COMPETITIONS (Hardcoded known competitions)
# ═══════════════════════════════════════════════════════════════════════════════

SEED_COMPETITIONS = [
    {
        "url": "https://design.adaptyvbio.com/",
        "source": "Adaptyv Bio",
        "title": "Protein Binder Design Competition – Round 3",
        "organizer": "Adaptyv Bio",
        "location": "Remote – wet-lab validation in Geneva",
        "team_size": "Individual or teams",
        "prizes": "Wet-lab synthesis & assay + $5,000 cash",
        "travel_grant": False,
        "registration": "Free",
        "eligibility": "Open to all",
        "end_date": "2025-06-30",
        "tags": ["Protein Design", "Binder", "Wet-Lab"],
        "description": "Design protein binders targeting disease-relevant targets. Top designs are synthesised and assayed by Adaptyv Bio's automated platform.",
        "how_to_apply": "Submit sequences through the online portal. Designs are evaluated computationally, and top candidates proceed to experimental validation.",
        "requirements": "Protein sequences in FASTA format. Must follow submission guidelines for chain length and complexity.",
        "contact": "support@adaptyvbio.com",
    },
    {
        "url": "https://predictioncenter.org/casp16/",
        "source": "CASP",
        "title": "CASP16 – Critical Assessment of Protein Structure Prediction",
        "organizer": "University of California San Diego",
        "location": "Global – results presented in Cancun, Mexico",
        "team_size": "Individual or academic group",
        "prizes": "Recognition + invited talk at CASP conference",
        "travel_grant": True,
        "registration": "Free",
        "eligibility": "Academic & industry",
        "end_date": "2025-08-15",
        "tags": ["Structure Prediction", "AlphaFold", "CASP"],
        "description": "The biennial 'Olympics' of protein structure prediction. Groups submit models for experimentally determined but unpublished target structures.",
        "how_to_apply": "Register on the CASP website, download target sequences, submit predictions through the online server or via email.",
        "requirements": "Predict 3D coordinates for target proteins. Acceptable formats: PDB, mmCIF.",
        "contact": "casp@predictioncenter.org",
    },
    {
        "url": "https://competition.igem.org/",
        "source": "iGEM Foundation",
        "title": "iGEM Grand Jamboree 2025",
        "organizer": "iGEM Foundation",
        "location": "Paris, France (Grand Jamboree) + regional hubs",
        "team_size": "Team of 5–20 students",
        "prizes": "Gold / Silver / Bronze medals + Special Awards",
        "travel_grant": True,
        "registration": "Paid – team registration fee applies",
        "eligibility": "Students (high-school through graduate)",
        "end_date": "2025-10-26",
        "tags": ["Synthetic Biology", "iGEM", "Gene Circuit"],
        "description": "Annual international synthetic biology competition. Teams engineer biological systems and present at the Grand Jamboree in Paris.",
        "how_to_apply": "Form a team, register on iGEM website, pay registration fee, document project on Wiki.",
        "requirements": "Team wiki, presentation, poster, and working biological project.",
        "contact": "competition@igem.org",
    },
    {
        "url": "https://cafa.iddo.org/",
        "source": "CAFA Consortium",
        "title": "CAFA6 – Critical Assessment of Functional Annotation",
        "organizer": "CAFA Consortium / Indiana University",
        "location": "Remote – results at ISMB 2025",
        "team_size": "Individual or group",
        "prizes": "Recognition + invited talk at ISMB/ECCB",
        "travel_grant": True,
        "registration": "Free",
        "eligibility": "Open to all",
        "end_date": "2025-06-01",
        "tags": ["Protein Function", "Annotation", "Machine Learning"],
        "description": "Community challenge to advance computational prediction of gene product functions across the tree of life.",
        "how_to_apply": "Register on CAFA website, download benchmark sets, submit predictions.",
        "requirements": "GO term predictions with confidence scores.",
        "contact": "cafa@iddo.org",
    },
    {
        "url": "https://www.nyas.org/events/2025/hack-the-genome/",
        "source": "New York Academy of Sciences",
        "title": "Hack the Genome 2025 – Computational Genomics Hackathon",
        "organizer": "New York Academy of Sciences",
        "location": "New York, USA (hybrid options)",
        "team_size": "Teams of 3–5",
        "prizes": "$10,000 + mentorship + publication",
        "travel_grant": True,
        "registration": "Free",
        "eligibility": "Students & early-career researchers",
        "end_date": "2025-04-30",
        "tags": ["Genomics", "Hackathon", "Machine Learning"],
        "description": "Weekend hackathon bringing together life scientists, computational researchers, and data scientists to solve genome biology challenges.",
        "how_to_apply": "Apply online with CV and motivation statement. Teams can be pre-formed or assigned.",
        "requirements": "In-person or remote participation. Laptop required.",
        "contact": "hackathon@nyas.org",
    },
    {
        "url": "https://dreamchallenges.org/",
        "source": "DREAM Challenges",
        "title": "DREAM Challenges – Open Systems Biology Problems",
        "organizer": "Sage Bionetworks / IBM",
        "location": "Remote",
        "team_size": "Individual or team",
        "prizes": "Publication co-authorship + recognition",
        "travel_grant": False,
        "registration": "Free",
        "eligibility": "Open to all",
        "end_date": "Rolling (check site)",
        "tags": ["Systems Biology", "Machine Learning", "Drug Discovery"],
        "description": "Ongoing series of challenges to catalyse community efforts to advance systems biology and translational medicine.",
        "how_to_apply": "Join Synapse platform, register for specific challenge, submit predictions.",
        "requirements": "Synapse account. Coding skills in Python/R recommended.",
        "contact": "dream@sagebionetworks.org",
    },
    {
        "url": "https://www.kaggle.com/competitions/leash-BELKA",
        "source": "Kaggle / Leash Bio",
        "title": "Leash Bio – BELKA Small Molecule Binding Prediction",
        "organizer": "Leash Bio / Kaggle",
        "location": "Online",
        "team_size": "Individual or team of up to 5",
        "prizes": "$50,000 prize pool",
        "travel_grant": False,
        "registration": "Free",
        "eligibility": "Open to all",
        "end_date": "2024-07-08",
        "tags": ["Drug Discovery", "Machine Learning", "Ligand"],
        "description": "Predict small molecule binding to three protein targets at unprecedented scale. 133M small molecules to explore.",
        "how_to_apply": "Register on Kaggle, join competition, download dataset, submit predictions.",
        "requirements": "Kaggle account. GPU access recommended.",
        "contact": "competitions@kaggle.com",
    },
    {
        "url": "https://www.embl.org/events/",
        "source": "EMBL",
        "title": "EMBL Computational Biology Symposium – Poster Prize",
        "organizer": "European Molecular Biology Laboratory",
        "location": "Heidelberg, Germany",
        "team_size": "Individual",
        "prizes": "€1,000 poster prize + free conference registration",
        "travel_grant": True,
        "registration": "Conference fee applies",
        "eligibility": "PhD students & postdocs",
        "end_date": "2025-09-15",
        "tags": ["Structural Biology", "Computational Biology"],
        "description": "Annual EMBL symposium with dedicated poster competition for early-career computational biologists.",
        "how_to_apply": "Submit abstract through conference portal. Indicate poster preference.",
        "requirements": "PhD student or postdoc status. Original research.",
        "contact": "events@embl.de",
    },
    {
        "url": "https://www.cameo3d.org/",
        "source": "CAMEO",
        "title": "CAMEO – Continuous Automated Model Evaluation",
        "organizer": "SIB Swiss Institute of Bioinformatics",
        "location": "Remote – continuous evaluation",
        "team_size": "Individual or group",
        "prizes": "Weekly benchmarking reports",
        "travel_grant": False,
        "registration": "Free",
        "eligibility": "Open to all",
        "end_date": "Continuous",
        "tags": ["Structure Prediction", "Benchmarking", "Continuous"],
        "description": "Continuous evaluation service for protein structure prediction methods. Weekly targets from PDB release.",
        "how_to_apply": "Register server, submit predictions weekly via API or web interface.",
        "requirements": "Automated prediction pipeline. Server must be registered.",
        "contact": "cameo@isb-sib.ch",
    },
    {
        "url": "https://alphafold.ebi.ac.uk/",
        "source": "AlphaFold DB",
        "title": "AlphaFold Protein Structure Database Challenge",
        "organizer": "DeepMind / EMBL-EBI",
        "location": "Remote",
        "team_size": "Individual",
        "prizes": "Recognition on leaderboard",
        "travel_grant": False,
        "registration": "Free",
        "eligibility": "Open to all",
        "end_date": "Continuous",
        "tags": ["AlphaFold", "Structure Prediction", "Database"],
        "description": "Community challenge to predict structures for proteins in AlphaFold DB. Compare your method against state-of-the-art.",
        "how_to_apply": "Download sequences from AFDB, submit predictions, upload to evaluation server.",
        "requirements": "Predictions in PDB format. Method documentation required.",
        "contact": "alphafold@ebi.ac.uk",
    },
    {
        "url": "https://biodesignchallenge.org/",
        "source": "Biodesign Challenge",
        "title": "Biodesign Challenge 2025",
        "organizer": "Biodesign Challenge Foundation",
        "location": "New York, USA (finals)",
        "team_size": "University teams",
        "prizes": "Exhibition at Museum of Modern Art + Awards",
        "travel_grant": True,
        "registration": "University participation fee",
        "eligibility": "University students (art, design, biology, engineering)",
        "end_date": "2025-06-15",
        "tags": ["Synthetic Biology", "Design", "Art"],
        "description": "International competition combining design and synthetic biology. Teams envision future biotechnological applications.",
        "how_to_apply": "University registers, forms interdisciplinary team, submits concept.",
        "requirements": "Design concept, prototypes, presentation at finals.",
        "contact": "info@biodesignchallenge.org",
    },
    {
        "url": "https://www.pdbj.org/csa/",
        "source": "PDBj",
        "title": "PDBj Coding Sprint for Algorithms",
        "organizer": "PDBj / Protein Data Bank Japan",
        "location": "Osaka, Japan (hybrid)",
        "team_size": "Individual or pair",
        "prizes": "Travel grant to ISMB/ECCB",
        "travel_grant": True,
        "registration": "Free",
        "eligibility": "Students and early-career researchers",
        "end_date": "2025-05-20",
        "tags": ["Programming", "Structural Biology", "PDB"],
        "description": "Algorithm development sprint focused on PDB data mining, visualization, and analysis tools.",
        "how_to_apply": "Submit CV and project proposal through PDBj portal.",
        "requirements": "Programming skills (Python/Java). Interest in structural biology.",
        "contact": "csa@pdbj.org",
    },
    {
        "url": "https://rosie.rosettacommons.org/",
        "source": "Rosetta Commons",
        "title": "ROSIE – Rosetta Online Server Evaluation",
        "organizer": "Rosetta Commons / University of Washington",
        "location": "Remote – continuous",
        "team_size": "Individual",
        "prizes": "Method benchmarking + co-authorship",
        "travel_grant": False,
        "registration": "Free",
        "eligibility": "Open to all",
        "end_date": "Continuous",
        "tags": ["Rosetta", "Protein Design", "Benchmarking"],
        "description": "Continuous evaluation platform for Rosetta-based protein design and structure prediction methods.",
        "how_to_apply": "Register on ROSIE, submit method for blind testing against weekly targets.",
        "requirements": "Rosetta protocol or custom method. Documentation required.",
        "contact": "rosie@uw.edu",
    },
    {
        "url": "https://www.ebi.ac.uk/pdbe/emdb/",
        "source": "EMDB",
        "title": "Cryo-EM Model Challenge",
        "organizer": "EMBL-EBI / EMDB",
        "location": "Remote",
        "team_size": "Individual or group",
        "prizes": "Recognition at EM meeting",
        "travel_grant": True,
        "registration": "Free",
        "eligibility": "Open to all",
        "end_date": "2025-07-30",
        "tags": ["Cryo-EM", "Structure", "Electron Microscopy"],
        "description": "Challenge to build atomic models from cryo-EM density maps. Tests modeling methods for membrane proteins and complexes.",
        "how_to_apply": "Download maps from EMDB, submit models, participate in validation.",
        "requirements": "Cryo-EM modeling software (ChimeraX, Coot, etc.).",
        "contact": "emdb@ebi.ac.uk",
    },
    {
        "url": "https://sbgrid.org/collaborations/",
        "source": "SBGrid",
        "title": "SBGrid Software Challenge",
        "organizer": "SBGrid Consortium / Harvard Medical School",
        "location": "Remote",
        "team_size": "Individual",
        "prizes": "Software deployment support + recognition",
        "travel_grant": False,
        "registration": "Free",
        "eligibility": "Open source developers",
        "end_date": "Rolling",
        "tags": ["Software", "Structural Biology", "Open Source"],
        "description": "Challenge to develop and optimize open-source software tools for structural biology.",
        "how_to_apply": "Submit software proposal through SBGrid portal. Code must be open source.",
        "requirements": "Open source license. Documentation and tests required.",
        "contact": "info@sbgrid.org",
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def infer_deadline(text: str) -> str:
    """Extract deadline from text with multiple pattern matching."""
    patterns = [
        r'deadline[:\s]+([A-Z][a-z]+ \d{1,2},?\s*\d{4})',
        r'deadline[:\s]+(\d{1,2}\s+[A-Z][a-z]+\s*\d{4})',
        r'closes?[:\s]+([A-Z][a-z]+ \d{1,2},?\s*\d{4})',
        r'due[:\s]+([A-Z][a-z]+ \d{1,2},?\s*\d{4})',
        r'submit by[:\s]+([A-Z][a-z]+ \d{1,2},?\s*\d{4})',
        r'registration[:\s]+([A-Z][a-z]+ \d{1,2},?\s*\d{4})',
        r'application[:\s]+([A-Z][a-z]+ \d{1,2},?\s*\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{2}/\d{2}/\d{4})',
        r'(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            date_str = m.group(1)
            try:
                # Try to normalize to ISO format
                dt = datetime.datetime.strptime(date_str, '%B %d, %Y')
                return dt.strftime('%Y-%m-%d')
            except:
                try:
                    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    return date_str
                except:
                    return date_str
    # Default: 90 days from now
    return (datetime.datetime.now() + datetime.timedelta(days=90)).strftime('%Y-%m-%d')

def extract_meta(text: str) -> Dict:
    """Extract rich metadata from competition text."""
    meta = {
        'team_size': 'Check rules',
        'location': 'Global / Online',
        'organizer': 'See link',
        'prizes': 'Recognition / Data',
        'travel_grant': False,
        'registration': 'Free',
        'eligibility': 'Open to all',
        'end_date': infer_deadline(text),
        'tags': [],
        'requirements': '',
        'how_to_apply': '',
        'contact': '',
    }
    
    # Team size extraction
    team_patterns = [
        r'team(?:s)?\s+of\s+(up\s+to\s+)?(\d+)',
        r'max(?:imum)?\s+(\d+)\s+(?:per\s+)?team',
        r'(?:up\s+to\s+)?(\d+)\s+members?',
        r'(?:up\s+to\s+)?(\d+)\s+people',
        r'individual(?:ly)?',
        r'solo',
    ]
    for p in team_patterns:
        m = re.search(p, text, re.I)
        if m:
            if 'individual' in p or 'solo' in p:
                meta['team_size'] = 'Individual only'
            elif m.group(1) and 'up to' in m.group(0).lower():
                meta['team_size'] = f'Up to {m.group(1 or m.group(2))} members'
            elif m.group(1):
                meta['team_size'] = f'Up to {m.group(1)} members'
            elif m.group(2):
                meta['team_size'] = f'Up to {m.group(2)} members'
            break
    
    # Travel grant detection
    travel_patterns = [
        r'travel\s+(?:grant|award|support|stipend|funding|assistance|reimbursement)',
        r'financial\s+assistance',
        r'funded\s+attendance',
        r'conference\s+travel',
        r'flight\s+covered',
        r'accommodation\s+provided',
    ]
    for p in travel_patterns:
        if re.search(p, text, re.I):
            meta['travel_grant'] = True
            break
    
    # Registration fee detection
    fee_patterns = [
        r'registration\s+fee[:\s]+\$?(\d+)',
        r'entry\s+fee[:\s]+\$?(\d+)',
        r'fee[:\s]+\$?(\d+)',
        r'cost[:\s]+\$?(\d+)',
        r'payment\s+required',
        r'paid\s+registration',
        r'non-refundable',
    ]
    free_patterns = [
        r'free\s+(?:to\s+)?(?:enter|participate|register|join)',
        r'no\s+(?:registration\s+)?fee',
        r'complimentary',
        r'gratis',
    ]
    
    is_free = any(re.search(p, text, re.I) for p in free_patterns)
    is_paid = any(re.search(p, text, re.I) for p in fee_patterns)
    
    if is_paid and not is_free:
        fee_match = re.search(r'\$?([\d,]+)\s*(?:USD|EUR|GBP)?', text, re.I)
        if fee_match:
            meta['registration'] = f'Paid – ${fee_match.group(1)} fee'
        else:
            meta['registration'] = 'Paid – see link'
    elif is_free:
        meta['registration'] = 'Free'
    
    # Prize extraction
    prize_patterns = [
        r'prize\s+(?:pool|money)?[:\s]+\$?([\d,]+(?:k|K)?)',
        r'\$([\d,]+(?:\s*(?:million|M|K|k))?)\s+(?:in\s+)?prizes',
        r'win\s+\$?([\d,]+)',
        r'award[:\s]+\$?([\d,]+)',
        r'cash\s+(?:prize|award)[:\s]+\$?([\d,]+)',
        r'grand\s+prize[:\s]+\$?([\d,]+)',
    ]
    prizes = []
    for p in prize_patterns:
        m = re.findall(p, text, re.I)
        prizes.extend(m)
    if prizes:
        meta['prizes'] = f'Prize pool: ${", $".join(prizes[:3])}'
    elif re.search(r'cash\s+prize|monetary\s+award|funding|grant', text, re.I):
        meta['prizes'] = 'Cash/Grant award (see link)'
    
    # Eligibility
    eligibility_patterns = [
        (r'student(?:s)?\s+(?:only|must|required)', 'Students only'),
        (r'undergraduate', 'Undergraduates'),
        (r'graduate\s+student', 'Graduate students'),
        (r'phd\s+student', 'PhD students'),
        (r'postdoc', 'Postdoctoral researchers'),
        (r'early[-\s]career', 'Early-career researchers'),
        (r'academic\s+(?:only|teams?|researchers?)', 'Academic teams'),
        (r'industry', 'Industry professionals allowed'),
        (r'open\s+to\s+all', 'Open to all'),
        (r'global', 'Global participation'),
    ]
    for pattern, label in eligibility_patterns:
        if re.search(pattern, text, re.I):
            meta['eligibility'] = label
            break
    
    # Location extraction
    cities = [
        'Amsterdam', 'Barcelona', 'Basel', 'Berlin', 'Boston', 'Brussels', 
        'Cambridge', 'Copenhagen', 'London', 'Los Angeles', 'Melbourne', 
        'Munich', 'New York', 'Osaka', 'Oxford', 'Paris', 'Rome', 'San Diego', 
        'San Francisco', 'Seattle', 'Singapore', 'Stockholm', 'Sydney', 
        'Tokyo', 'Toronto', 'Vancouver', 'Vienna', 'Zurich', 'Heidelberg',
        'Bethesda', 'Rockville', 'College Park', 'Pittsburgh', 'Atlanta'
    ]
    found_cities = [c for c in cities if c.lower() in text.lower()]
    if found_cities:
        meta['location'] = f'Physical – {", ".join(found_cities[:2])}'
    elif re.search(r'remote|online|virtual|worldwide|global', text, re.I):
        meta['location'] = 'Remote / Online'
    
    # Tag extraction
    tag_keywords = {
        'AlphaFold': r'alphafold',
        'Rosetta': r'rosetta',
        'ESMFold': r'esmfold',
        'De-Novo': r'de\s+novo',
        'Drug Discovery': r'drug\s+discovery',
        'iGEM': r'igem',
        'Synthetic Biology': r'synthetic\s+biology',
        'Docking': r'docking',
        'NLP': r'nlp|natural\s+language',
        'Machine Learning': r'machine\s+learning|ml\b',
        'Deep Learning': r'deep\s+learning',
        'Cryo-EM': r'cryo[\s-]?em',
        'Peptide': r'peptide',
        'Antibody': r'antibody',
        'Enzyme': r'enzyme',
        'Ligand': r'ligand',
        'Binder': r'binder',
        'Genomics': r'genomics',
        'Structural Biology': r'structural\s+biology',
        'Bioinformatics': r'bioinformatics',
        'Systems Biology': r'systems\s+biology',
        'Metabolic Engineering': r'metabolic\s+engineering',
        'Gene Circuit': r'gene\s+circuit',
        'Hackathon': r'hackathon',
        'Benchmark': r'benchmark',
        'Wet-Lab': r'wet[\s-]?lab|experimental|validation',
    }
    for tag, pattern in tag_keywords.items():
        if re.search(pattern, text, re.I):
            meta['tags'].append(tag)
    
    return meta

def fetch_scrape_targets(db: Dict):
    """Scrape competition-specific websites."""
    for name, cfg in SCRAPE_TARGETS.items():
        print(f"  Scraping: {name}...")
        try:
            res = requests.get(cfg['url'], timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Find competition links
            for a in soup.find_all('a', href=True):
                if cfg['link_pattern'] in a['href']:
                    href = a['href']
                    url = href if href.startswith('http') else urljoin(cfg['base'], href)
                    
                    # Get title and description
                    title = a.get_text(separator=' ', strip=True)
                    if not title:
                        # Try parent or nearby elements
                        parent = a.find_parent(['h1', 'h2', 'h3', 'div', 'article'])
                        if parent:
                            title = parent.get_text(separator=' ', strip=True)[:100]
                    
                    if url not in db and title and len(title) > 10:
                        # Get more context
                        context = ''
                        if a.parent:
                            context = a.parent.get_text(separator=' ', strip=True)
                        
                        meta = extract_meta(title + ' ' + context)
                        
                        db[url] = {
                            'source': name,
                            'title': title[:120],
                            'link': url,
                            'organizer': cfg.get('organizer', meta['organizer']),
                            'location': cfg.get('location', meta['location']),
                            'team_size': meta['team_size'],
                            'prizes': cfg.get('prizes', meta['prizes']),
                            'travel_grant': meta['travel_grant'],
                            'registration': meta['registration'],
                            'eligibility': meta['eligibility'],
                            'end_date': meta['end_date'],
                            'tags': meta['tags'],
                            'description': context[:200] + '...' if len(context) > 200 else context,
                            'how_to_apply': '',
                            'requirements': '',
                            'contact': '',
                            'added_date': datetime.datetime.now().isoformat(),
                        }
                        print(f"    Added: {title[:60]}...")
                        
        except Exception as e:
            print(f"    ✗ {name}: {e}")

def fetch_rss(db: Dict):
    """Fetch and parse RSS feeds."""
    for name, url in RSS_SOURCES.items():
        print(f"  Fetching: {name}...")
        try:
            feed = feedparser.parse(url, timeout=20)
            
            for entry in feed.entries:
                # Combine title and summary for keyword matching
                text = entry.get('title', '') + ' ' + entry.get('summary', '')
                text_lower = text.lower()
                
                # Check if relevant
                if any(k in text_lower for k in KEYWORDS):
                    link = entry.get('link', '')
                    if not link or link in db:
                        continue
                    
                    # Extract metadata
                    meta = extract_meta(text)
                    
                    # Get published date
                    pub_date = entry.get('published', entry.get('updated', ''))
                    
                    db[link] = {
                        'source': name,
                        'title': entry.get('title', 'No title')[:120],
                        'link': link,
                        'organizer': meta['organizer'],
                        'location': meta['location'],
                        'team_size': meta['team_size'],
                        'prizes': meta['prizes'],
                        'travel_grant': meta['travel_grant'],
                        'registration': meta['registration'],
                        'eligibility': meta['eligibility'],
                        'end_date': meta['end_date'],
                        'tags': meta['tags'],
                        'description': entry.get('summary', 'No description')[:250],
                        'how_to_apply': '',
                        'requirements': '',
                        'contact': '',
                        'published': pub_date,
                        'added_date': datetime.datetime.now().isoformat(),
                    }
                    
        except Exception as e:
            print(f"    ✗ {name}: {e}")

def inject_seeds(db: Dict):
    """Inject hardcoded seed competitions."""
    for comp in SEED_COMPETITIONS:
        url = comp.pop('url')
        if url not in db:
            db[url] = comp
            db[url]['link'] = url
            db[url]['added_date'] = datetime.datetime.now().isoformat()

# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED HTML GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_html(db: Dict):
    """Generate interactive HTML with rich features."""
    
    # Collect all tags
    all_tags = sorted({t for item in db.values() for t in item.get('tags', [])})
    
    # Generate filter buttons
    filter_btns = '<button class="filter-btn active" data-filter="all">All Competitions</button>'
    filter_btns += '<button class="filter-btn grant-filter" data-filter="grant">✈ Travel Grants</button>'
    filter_btns += '<button class="filter-btn free-filter" data-filter="free">🆓 Free Entry</button>'
    
    for tag in all_tags:
        slug = tag.lower().replace(' ', '-')
        filter_btns += f'<button class="filter-btn" data-filter="{slug}">{tag}</button>'
    
    # Generate competition cards
    cards_html = ""
    for url, item in db.items():
        tags = item.get('tags', [])
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in tags)
        tags_data = " ".join(tags).lower()
        
        # Badges
        grant_badge = '<span class="badge grant">✈ Travel Grant</span>' if item.get('travel_grant') else ''
        free_badge = '<span class="badge free">FREE</span>' if 'free' in str(item.get('registration', '')).lower() else ''
        
        # Status indicator
        try:
            end_date = datetime.datetime.strptime(item.get('end_date', '2099-12-31'), '%Y-%m-%d')
            days_left = (end_date - datetime.datetime.now()).days
            if days_left < 0:
                status = '<span class="status expired">Expired</span>'
            elif days_left < 7:
                status = f'<span class="status urgent">{days_left} days left!</span>'
            elif days_left < 30:
                status = f'<span class="status closing">{days_left} days left</span>'
            else:
                status = f'<span class="status open">Open</span>'
        except:
            status = '<span class="status open">Open</span>'
        
        # Create card with modal trigger
        cards_html += f'''
        <div class="card" data-tags="{tags_data}" data-grant="{str(item.get('travel_grant', False)).lower()}" 
             data-free="{'true' if 'free' in str(item.get('registration', '')).lower() else 'false'}"
             data-title="{item['title'].lower().replace('"', '&quot;')}">
          <div class="card-header">
            <div class="card-badges">{grant_badge} {free_badge} {status}</div>
            <span class="source-chip">{item['source']}</span>
          </div>
          <h3 class="card-title">{item['title']}</h3>
          <p class="card-desc">{item.get('description', 'Click for details')[:180]}...</p>
          <div class="quick-meta">
            <span>📍 {item.get('location', 'TBD')}</span>
            <span>👥 {item.get('team_size', 'TBD')}</span>
            <span>📅 {item.get('end_date', 'TBD')}</span>
          </div>
          <div class="card-tags">{tags_html}</div>
          <div class="card-actions">
            <button class="btn-details" onclick="openModal('{url}')">📋 Details</button>
            <a href="{url}" target="_blank" rel="noopener" class="btn-apply">Apply →</a>
          </div>
        </div>
        '''
    
    # Generate modal data (JSON for JavaScript)
    modal_data = {}
    for url, item in db.items():
        modal_data[url] = {
            'title': item.get('title', ''),
            'source': item.get('source', ''),
            'organizer': item.get('organizer', ''),
            'location': item.get('location', ''),
            'team_size': item.get('team_size', ''),
            'prizes': item.get('prizes', ''),
            'registration': item.get('registration', ''),
            'eligibility': item.get('eligibility', ''),
            'end_date': item.get('end_date', ''),
            'description': item.get('description', ''),
            'how_to_apply': item.get('how_to_apply', ''),
            'requirements': item.get('requirements', ''),
            'contact': item.get('contact', ''),
            'tags': item.get('tags', []),
            'travel_grant': item.get('travel_grant', False),
        }
    
    # Count statistics
    total = len(db)
    grants = sum(1 for v in db.values() if v.get('travel_grant'))
    free = sum(1 for v in db.values() if 'free' in str(v.get('registration', '')).lower())
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Protein Design & Bioinformatics Competitions</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #0a0f1a;
  --surface: #111827;
  --surface2: #1f2937;
  --surface3: #374151;
  --border: rgba(99,179,237,0.15);
  --accent: #3b82f6;
  --accent2: #06b6d4;
  --accent3: #8b5cf6;
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --text: #f3f4f6;
  --text2: #9ca3af;
  --text3: #6b7280;
  --card-r: 16px;
  --transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: 'Inter', sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  line-height: 1.6;
}}

body::before {{
  content: '';
  position: fixed;
  inset: 0;
  background: 
    radial-gradient(ellipse 80% 50% at 50% -10%, rgba(59,130,246,0.08) 0%, transparent 50%),
    radial-gradient(ellipse 40% 30% at 90% 90%, rgba(139,92,246,0.06) 0%, transparent 40%);
  pointer-events: none;
  z-index: 0;
}}

/* Header */
header {{
  position: relative;
  z-index: 1;
  padding: 3rem 2rem 2rem;
  text-align: center;
  border-bottom: 1px solid var(--border);
}}

.logo {{
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}}

.logo-icon {{
  font-size: 2.5rem;
  filter: drop-shadow(0 0 20px rgba(59,130,246,0.5));
}}

h1 {{
  font-size: clamp(1.75rem, 4vw, 2.75rem);
  font-weight: 700;
  background: linear-gradient(135deg, #fff 0%, #60a5fa 50%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}}

.subtitle {{
  color: var(--text2);
  font-size: 1rem;
  max-width: 600px;
  margin: 0 auto;
}}

/* Stats Bar */
.stats-bar {{
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-top: 2rem;
  flex-wrap: wrap;
}}

.stat {{
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--surface);
  border-radius: var(--card-r);
  border: 1px solid var(--border);
}}

.stat-num {{
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--accent);
  font-family: 'JetBrains Mono', monospace;
}}

.stat-label {{
  font-size: 0.75rem;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}}

/* Controls */
.controls {{
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(10,15,26,0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  padding: 1.25rem 2rem;
}}

.search-row {{
  display: flex;
  gap: 1rem;
  max-width: 1400px;
  margin: 0 auto 1rem;
}}

.search-input {{
  flex: 1;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--text);
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  padding: 0.75rem 1rem;
  outline: none;
  transition: var(--transition);
}}

.search-input:focus {{
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}}

.search-input::placeholder {{ color: var(--text3); }}

.filter-bar {{
  display: flex;
  gap: 0.5rem;
  max-width: 1400px;
  margin: 0 auto;
  flex-wrap: wrap;
}}

.filter-btn {{
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--text2);
  font-family: 'Inter', sans-serif;
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.4rem 1rem;
  cursor: pointer;
  transition: var(--transition);
  white-space: nowrap;
}}

.filter-btn:hover {{
  border-color: var(--accent);
  color: var(--accent);
}}

.filter-btn.active {{
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}}

.filter-btn.grant-filter.active {{
  background: var(--success);
  border-color: var(--success);
}}

.filter-btn.free-filter.active {{
  background: var(--accent2);
  border-color: var(--accent2);
}}

/* Main Grid */
.main {{
  position: relative;
  z-index: 1;
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}}

.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 1.5rem;
}}

/* Card */
.card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--card-r);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  transition: var(--transition);
  position: relative;
}}

.card:hover {{
  transform: translateY(-4px);
  border-color: rgba(59,130,246,0.3);
  box-shadow: 0 20px 40px rgba(0,0,0,0.3), 0 0 0 1px rgba(59,130,246,0.2);
}}

.card.hidden {{ display: none; }}

.card-header {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.5rem;
}}

.card-badges {{
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}}

.badge {{
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  letter-spacing: 0.03em;
}}

.badge.grant {{
  background: rgba(16,185,129,0.15);
  color: var(--success);
  border: 1px solid rgba(16,185,129,0.3);
}}

.badge.free {{
  background: rgba(6,182,212,0.15);
  color: var(--accent2);
  border: 1px solid rgba(6,182,212,0.3);
}}

.status {{
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}}

.status.open {{
  background: rgba(59,130,246,0.15);
  color: #60a5fa;
}}

.status.closing {{
  background: rgba(245,158,11,0.15);
  color: #fbbf24;
}}

.status.urgent {{
  background: rgba(239,68,68,0.15);
  color: #f87171;
  animation: pulse 2s infinite;
}}

.status.expired {{
  background: var(--surface3);
  color: var(--text3);
}}

@keyframes pulse {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.7; }}
}}

.source-chip {{
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--accent);
  background: rgba(59,130,246,0.1);
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
}}

.card-title {{
  font-size: 1.1rem;
  font-weight: 600;
  line-height: 1.4;
  color: var(--text);
}}

.card-desc {{
  font-size: 0.875rem;
  color: var(--text2);
  line-height: 1.6;
}}

.quick-meta {{
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  font-size: 0.8rem;
  color: var(--text3);
}}

.quick-meta span {{
  display: flex;
  align-items: center;
  gap: 0.25rem;
}}

.card-tags {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: auto;
  padding-top: 0.5rem;
}}

.tag {{
  font-size: 0.7rem;
  font-weight: 500;
  background: var(--surface2);
  color: var(--text2);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.2rem 0.5rem;
}}

.card-actions {{
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
}}

.btn-details, .btn-apply {{
  flex: 1;
  padding: 0.6rem 1rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: var(--transition);
  text-align: center;
  text-decoration: none;
  border: none;
}}

.btn-details {{
  background: var(--surface2);
  color: var(--text);
}}

.btn-details:hover {{
  background: var(--surface3);
}}

.btn-apply {{
  background: linear-gradient(135deg, var(--accent), var(--accent3));
  color: white;
}}

.btn-apply:hover {{
  transform: scale(1.02);
  box-shadow: 0 4px 20px rgba(59,130,246,0.4);
}}

/* Modal */
.modal-overlay {{
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.8);
  backdrop-filter: blur(8px);
  z-index: 1000;
  justify-content: center;
  align-items: center;
  padding: 2rem;
}}

.modal-overlay.active {{ display: flex; }}

.modal {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  max-width: 700px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
}}

.modal-header {{
  padding: 1.5rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}}

.modal-title {{
  font-size: 1.4rem;
  font-weight: 600;
}}

.modal-close {{
  background: var(--surface2);
  border: none;
  color: var(--text2);
  width: 32px;
  height: 32px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.2rem;
  transition: var(--transition);
}}

.modal-close:hover {{
  background: var(--danger);
  color: white;
}}

.modal-body {{
  padding: 1.5rem;
}}

.meta-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}}

.meta-item {{
  background: var(--surface2);
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid var(--border);
}}

.meta-label {{
  font-size: 0.7rem;
  text-transform: uppercase;
  color: var(--text3);
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}}

.meta-value {{
  font-size: 0.95rem;
  color: var(--text);
  font-weight: 500;
}}

.modal-section {{
  margin-bottom: 1.5rem;
}}

.modal-section h4 {{
  font-size: 0.8rem;
  text-transform: uppercase;
  color: var(--text3);
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}}

.modal-section p {{
  color: var(--text2);
  font-size: 0.9rem;
  line-height: 1.7;
}}

.modal-actions {{
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid var(--border);
}}

.modal-btn {{
  flex: 1;
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
  text-align: center;
  text-decoration: none;
  border: none;
  font-size: 0.95rem;
}}

.modal-btn-primary {{
  background: linear-gradient(135deg, var(--accent), var(--accent3));
  color: white;
}}

.modal-btn-primary:hover {{
  transform: scale(1.02);
  box-shadow: 0 4px 20px rgba(59,130,246,0.4);
}}

.modal-btn-secondary {{
  background: var(--surface2);
  color: var(--text);
}}

.modal-btn-secondary:hover {{
  background: var(--surface3);
}}

/* Footer */
footer {{
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 3rem 2rem;
  color: var(--text3);
  font-size: 0.85rem;
  border-top: 1px solid var(--border);
}}

footer a {{
  color: var(--accent);
  text-decoration: none;
}}

footer a:hover {{
  text-decoration: underline;
}}

/* Responsive */
@media (max-width: 768px) {{
  .grid {{ grid-template-columns: 1fr; }}
  .stats-bar {{ gap: 1rem; }}
  .modal {{
    margin: 1rem;
    max-height: calc(100vh - 2rem);
  }}
}}

/* Empty state */
.empty-state {{
  grid-column: 1/-1;
  text-align: center;
  padding: 4rem;
  color: var(--text3);
}}

.empty-state-icon {{
  font-size: 4rem;
  margin-bottom: 1rem;
}}
</style>
</head>
<body>

<header>
  <div class="logo">
    <span class="logo-icon">🧬</span>
    <h1>Protein Design & Bioinformatics Competitions</h1>
  </div>
  <p class="subtitle">Comprehensive aggregator of competitions, hackathons, and challenges in protein science, structural biology, and computational biotechnology</p>
  <div class="stats-bar">
    <div class="stat"><span class="stat-num">{total}</span><span class="stat-label">Total</span></div>
    <div class="stat"><span class="stat-num">{grants}</span><span class="stat-label">Travel Grants</span></div>
    <div class="stat"><span class="stat-num">{free}</span><span class="stat-label">Free Entry</span></div>
  </div>
</header>

<div class="controls">
  <div class="search-row">
    <input class="search-input" id="search" type="text" placeholder="🔍 Search competitions, organizations, keywords...">
  </div>
  <div class="filter-bar" id="filter-bar">
    {filter_btns}
  </div>
</div>

<main class="main">
  <div class="grid" id="grid">
    {cards_html}
  </div>
</main>

<!-- Modal -->
<div class="modal-overlay" id="modal" onclick="closeModal(event)">
  <div class="modal" onclick="event.stopPropagation()">
    <div class="modal-header">
      <h2 class="modal-title" id="modal-title">Competition Details</h2>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <div class="modal-body" id="modal-body">
      <!-- Dynamic content -->
    </div>
    <div class="modal-actions">
      <button class="modal-btn modal-btn-secondary" onclick="closeModal()">Close</button>
      <a class="modal-btn modal-btn-primary" id="modal-apply" href="#" target="_blank">Apply Now →</a>
    </div>
  </div>
</div>

<footer>
  <p>Updated daily via automated aggregation | Sources: CASP, iGEM, Kaggle, DREAM, EMBL, NIH, ERC, and 50+ scientific feeds</p>
  <p style="margin-top: 0.5rem;">Built with ❤️ for the protein science community</p>
</footer>

<script>
const competitionData = {json.dumps(modal_data, ensure_ascii=False)};

const cards = Array.from(document.querySelectorAll('.card'));
const grid = document.getElementById('grid');
const search = document.getElementById('search');
const filterBar = document.getElementById('filter-bar');
let activeFilter = 'all';

function applyFilters() {{
  const q = search.value.toLowerCase().trim();
  let visible = [];
  
  cards.forEach(c => {{
    const title = c.dataset.title || '';
    const tags = c.dataset.tags || '';
    const hasGrant = c.dataset.grant === 'true';
    const isFree = c.dataset.free === 'true';
    
    let show = true;
    if (activeFilter === 'grant') show = hasGrant;
    else if (activeFilter === 'free') show = isFree;
    else if (activeFilter !== 'all') show = tags.includes(activeFilter.replace(/-/g, ' '));
    
    if (q && !title.includes(q) && !tags.includes(q)) show = false;
    
    c.classList.toggle('hidden', !show);
    if (show) visible.push(c);
  }});
  
  // Empty state
  let empty = grid.querySelector('.empty-state');
  if (visible.length === 0) {{
    if (!empty) {{
      empty = document.createElement('div');
      empty.className = 'empty-state';
      empty.innerHTML = '<div class="empty-state-icon">🔬</div><p>No competitions match your filters.</p><p style="font-size: 0.9rem; margin-top: 0.5rem;">Try adjusting your search or filters</p>';
      grid.appendChild(empty);
    }}
  }} else if (empty) {{
    empty.remove();
  }}
}}

filterBar.addEventListener('click', e => {{
  const btn = e.target.closest('.filter-btn');
  if (!btn) return;
  
  activeFilter = btn.dataset.filter;
  filterBar.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  applyFilters();
}});

search.addEventListener('input', applyFilters);

// Modal functions
function openModal(url) {{
  const data = competitionData[url];
  if (!data) return;
  
  document.getElementById('modal-title').textContent = data.title;
  
  const badges = [];
  if (data.travel_grant) badges.push('<span class="badge grant">✈ Travel Grant</span>');
  if (data.registration?.toLowerCase().includes('free')) badges.push('<span class="badge free">FREE</span>');
  
  const tagsHtml = (data.tags || []).map(t => `<span class="tag">${{t}}</span>`).join('');
  
  document.getElementById('modal-body').innerHTML = `
    <div style="margin-bottom: 1rem;">${{badges.join(' ')}}</div>
    <div class="meta-grid">
      <div class="meta-item">
        <div class="meta-label">Organizer</div>
        <div class="meta-value">${{data.organizer || 'TBD'}}</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Location</div>
        <div class="meta-value">${{data.location || 'TBD'}}</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Team Size</div>
        <div class="meta-value">${{data.team_size || 'TBD'}}</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Deadline</div>
        <div class="meta-value">${{data.end_date || 'TBD'}}</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Prizes</div>
        <div class="meta-value">${{data.prizes || 'See details'}}</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Registration</div>
        <div class="meta-value">${{data.registration || 'See details'}}</div>
      </div>
    </div>
    
    <div class="modal-section">
      <h4>Description</h4>
      <p>${{data.description || 'No description available.'}}</p>
    </div>
    
    ${{data.how_to_apply ? `
    <div class="modal-section">
      <h4>How to Apply</h4>
      <p>${{data.how_to_apply}}</p>
    </div>
    ` : ''}}
    
    ${{data.requirements ? `
    <div class="modal-section">
      <h4>Requirements</h4>
      <p>${{data.requirements}}</p>
    </div>
    ` : ''}}
    
    ${{data.contact ? `
    <div class="modal-section">
      <h4>Contact</h4>
      <p>${{data.contact}}</p>
    </div>
    ` : ''}}
    
    <div style="margin-top: 1rem;">${{tagsHtml}}</div>
  `;
  
  document.getElementById('modal-apply').href = url;
  document.getElementById('modal').classList.add('active');
  document.body.style.overflow = 'hidden';
}}

function closeModal(e) {{
  if (!e || e.target.id === 'modal') {{
    document.getElementById('modal').classList.remove('active');
    document.body.style.overflow = '';
  }}
}}

// Close on escape key
document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') closeModal();
}});

applyFilters();
</script>

</body>
</html>'''
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'\n✓ index.html generated with {len(db)} competitions')
    print(f'  - Travel grants: {grants}')
    print(f'  - Free entry: {free}')

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print('=' * 70)
    print('Protein Design & Bioinformatics Competition Aggregator v2.0')
    print('=' * 70)
    
    db = load_db()
    print(f'\nLoaded {len(db)} existing entries')
    
    print('\nInjecting seed competitions...')
    inject_seeds(db)
    
    print('\nScraping competition websites...')
    fetch_scrape_targets(db)
    
    print('\nFetching RSS feeds...')
    fetch_rss(db)
    
    print(f'\nSaving database ({len(db)} total entries)...')
    save_db(db)
    
    print('\nGenerating HTML...')
    generate_html(db)
    
    print('\n' + '=' * 70)
    print('Done! Open index.html to view results')
    print('=' * 70)
