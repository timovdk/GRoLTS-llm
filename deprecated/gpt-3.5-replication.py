from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
import pandas as pd
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import dotenv
dotenv.load_dotenv()
from tqdm import tqdm
tqdm.pandas()

NUM_PAPERS = 38
EXP_ID = 2
RUN_DOC_EMBEDDINGS = False

DATA_PATH = './data/'
CHROMA_PATH = "./chroma/chroma_text-embedding-ada-002-500"
PROMPT_TEMPLATE = """
You are a helpful assistant assessing the quality of academic papers. Answer the question with YES or NO. Write nothing else before or after.
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

questions = {}
if EXP_ID == 0:
    questions = {
    0:      "Is the metric of time used in the statistical model reported?",
    1:      "Is information presented about the mean and variance of time within a wave?",
    2:      "Is the missing data mechanism reported?",
    3:      "Is a description provided of what variables are related to attrition/missing data?",
    4:      "Is a description provided of how missing data in the analyses were dealt with?",
    5:      "Is information about the distribution of the observed variables included?",
    6:      "Is the software mentioned?",
    7:      "Are alternative specifications of within-class heterogeneity considered (e.g., LGCA vs. LGMM) and clearly documented?",
    8:      "Are alternative specifications of the between-class differences in variancecovariance matrix structure considered and clearly documented?",
    9:      "Are alternative shape/functional forms of the trajectories described?",
    10:     "If covariates have been used, can analyses still be replicated?",
    11:     "Is information reported about the number of random start values and final iterations included?",
    12:     "Are the model comparison (and selection) tools described from a statistical perspective?",
    13:     "Are the total number of fitted models reported, including a one-class solution?",
    14:     "Are the number of cases per class reported for each model (absolute sample size, or proportion)?",
    15:     "If classification of cases in a trajectory is the goal, is entropy reported?",
    #16:    "Is a plot included with the estimated mean trajectories of the final solution?",
    #17:    "Are plots included with the estimated mean trajectories for each model?",
    #18:    "Is a plot included of the combination of estimated means of the final model and the observed individual trajectories split out for each latent class?",
    19:     "Are characteristics of the final class solution numerically described (i.e., means, SD/SE, n, CI, etc.)?",
    #20:    "Are the syntax files available (either in the appendix, supplementary materials, or from the authors)?"
    }

elif EXP_ID == 1:
    questions = {
    0:      "Is the metric or unit of time used in the statistical model reported?",
    1:      "Is information presented about the mean and variance of time within a wave?",
    2:      "Is the missing data mechanism reported?",
    3:      "Is a description provided of what variables are related to attrition/missing data?",
    4:      "Is a description provided of how missing data in the analyses were dealt with?",
    5:      "Is information about the distribution of the observed variables included?",
    6:      "Is the software that was used for the statistical analysis mentioned?",
    7:      "Are alternative specifications of within-class heterogeneity considered (e.g., LGCA vs. LGMM) and clearly documented?",
    8:      "Are alternative specifications of the between-class differences in variancecovariance matrix structure considered and clearly documented?",
    9:      "Are alternative shape/functional forms of the trajectories described?",
    10:     "If covariates or predictors have been used, is it done in such a way that the analyses could be replicated?",
    11:     "Is information reported about the number of random start values and final iterations included?",
    12:     "Are the model comparison (and selection) tools described from a statistical perspective?",
    13:     "Are the total number of fitted models reported, including a one-class solution?",
    14:     "Are the number of cases per class reported for each model (absolute sample size, or proportion)?",
    15:     "If classification of cases in a trajectory is the goal, is entropy reported?",
    #16:    "Is a plot included with the estimated mean trajectories of the final solution?",
    #17:    "Are plots included with the estimated mean trajectories for each model?",
    #18:    "Is a plot included of the combination of estimated means of the final model and the observed individual trajectories split out for each latent class?",
    19:     "Are characteristics of the final class solution numerically described (i.e., means, SD/SE, n, CI, etc.)?",
    #20:    "Are the syntax files available (either in the appendix, supplementary materials, or from the authors)?"
}

elif EXP_ID == 2:
    questions = {
    0:    "Is the metric or unit of time used in the statistical model reported? (i.e., hours, days, weeks, months, years, etc.)",
    1:    "Is information presented about the mean and variance of time within a wave?(mean and variance of: within measurement occasion, mean and variance of: within a period of time, etc.)",
    2:    "Is the missing data mechanism reported? (i.e., missing at random (MAR), Missing not at random (MNAR), missing completely at random (MCAR), etc.) ",
    3:    "Is a description provided of what variables are related to attrition/missing data? (i.e., a dropout effect, auxillary variables, skip patterns, etc.)",
    4:    "Is a description provided of how missing data in the analyses were dealt with?(i.e., List wise deletion, multiple imputation, Full information maximum likelihood (FIML) etc.)",
    5:    "Is information about the distribution of the observed variables included? (i.e., tests for normally distributed variables within classes, multivariarte normality, etc.) ",
    6:    "Is the software that was used for the statistical analysis mentioned? (i.e., Mplus, R, etc.)",
    7:    "Are alternative specifications of within-class heterogeneity considered (e.g., LGCA vs. LGMM) and clearly documented?",
    8:    "Are alternative specifications of the between-class differences in variance covariance matrix structure considered and clearly documented? (i.e., constrained accros subgroups, fixed accross subgroups, etc.)",
    9:    "Are alternative shape/functional forms of the trajectories described? (e.g., was it tested whether a quadratic trend or a non-linear form would fit the data better)",
    10:    "If covariates or predictors have been used, is it done in such a way that the analyses could be replicated? (e.g., was it reported they used time-varying or time-invariant covariates at the level of the dependent or independent variables)",
    11:    "Is information reported about the number of random start values and final iterations included? (e.g., If ML has been used to estimate the latent trajectory model, then it should be reported if the final class solution has converged to the maximum of the ML distribution and not on a local maxima.)",
    12:    "Are the model comparison (and selection) tools described from a statistical perspective? (i.e., BIC, AIC, etc.)",
    13:    "Are the total number of fitted models reported, including a one-class solution?",
    14:    "Are the number of cases per class reported for each model (absolute sample size, sample size per class or proportion)?",
    15:    "If classification of cases in a trajectory is the goal, is entropy reported? (i.e., the relative entropy value, the number of misclassifications per model)",
    #16:   "Is a plot included with the estimated mean trajectories of the final solution?",
    #17:   "Are plots included with the estimated mean trajectories for each model?",
    #18:   "Is a plot included of the combination of estimated means of the final model and the observed individual trajectories split out for each latent class?",
    19:    "Are characteristics of the final class solution numerically described (i.e., means, SD/SE, n, CI, etc.)?",
    #20:   "Are the syntax files available (either in the appendix, supplementary materials, or from the authors)?"
}

else:
    print("ERROR: No questions defined")
    exit(1)

def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    return chunks

def save_to_chroma(docs: list[Document], ids):
    db = Chroma.from_documents(
        docs, OpenAIEmbeddings(model='text-embedding-ada-002'), persist_directory=CHROMA_PATH
    )
    print(f"Saved {len(docs)} chunks to {CHROMA_PATH}.")

def generate_output(paper_id, question_id):    
    embedding_function = OpenAIEmbeddings(model='text-embedding-ada-002')
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_relevance_scores(questions[question_id], k=3, filter={'source': str('./data/' + str(paper_id) + '.pdf')})
    if len(results) == 0 or results[0][1] < 0.6:
        print(f"Unable to find matching results.")

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=questions[question_id])

    model = ChatOpenAI(model='gpt-3.5-turbo')
    response_text = model.invoke(prompt)
    return response_text.content

# Create DataFrame
df = pd.DataFrame(columns=list(questions.keys()))
df['Paper'] = range(NUM_PAPERS)

docs = []
ids = []
# Fill other columns with empty values
for index in range(NUM_PAPERS):
    df.loc[index, questions.keys()] = ''

if RUN_DOC_EMBEDDINGS:
    for index in range(NUM_PAPERS):
        loader = PyPDFLoader(str(DATA_PATH + str(index) + ".pdf"))
        pages = loader.load()
        splitted_text = split_text(pages)
        save_to_chroma(splitted_text, index)

def fill_cells(row):
    paper_id = row['Paper']
    for q_id, _ in row.items():
        if q_id != 'Paper':
            row[q_id] = generate_output(paper_id,q_id)
    return row


# Apply the function to each cell in the DataFrame
df = df.progress_apply(fill_cells, axis=1)
df.to_csv('./data_out/output' + str(EXP_ID) + '.csv', index=False)
