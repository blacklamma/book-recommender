import gradio as gr
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_chroma import Chroma
import os

load_dotenv(override=True)

books = pd.read_csv("books_with_emotions.csv")

books["large_thumbnail"] = books["thumbnail"] + "&fife=w800"
books["large_thumbnail"] = np.where(
    books["large_thumbnail"].isna(),
    "cover-not-found.jpg",
    books["large_thumbnail"]
)
raw_documents = TextLoader("tagged_descriptions.txt", encoding="utf-8").load()
text_splitter = CharacterTextSplitter(separator="\n", chunk_size=0, chunk_overlap=0)
documents = text_splitter.split_documents(raw_documents)
db_books = Chroma.from_documents(documents, OpenAIEmbeddings())

def retrieve_semantic_recommendations(
        query: str,
        category: str = None,
        tone: str = None,
        initial_top_k: int = 50,
        final_top_k: int = 16,
) -> pd.DataFrame:
    recs = db_books.similarity_search(query, k=initial_top_k)
    books_list = [int(rec.page_content.strip('"').split()[0].rstrip(':')) for rec in recs]
    book_recs = books[books["isbn13"].isin(books_list)].head(final_top_k)
    if category != "All":
        book_recs = book_recs[book_recs["simple_categories"] == category][:final_top_k]
    else:
        book_recs = book_recs.head(final_top_k)
    
    if tone == "Happy":
        book_recs.sort_values(by="joy", ascending=False, inplace=True)
    elif tone == "Surprising":
        book_recs.sort_values(by="surprise", ascending=False, inplace=True)
    elif tone == "Angry":
        book_recs.sort_values(by="anger", ascending=False, inplace=True)
    elif tone == "Suspenseful":
        book_recs.sort_values(by="fear", ascending=False, inplace=True)
    elif tone == "Sad":
        book_recs.sort_values(by="sadness", ascending=False, inplace=True)
    return book_recs


def recommend_books(
        query: str,
        category: str = None,
        tone: str = None
):
    recommendations = retrieve_semantic_recommendations(query, category, tone)
    result = []
    for _, row in recommendations.iterrows():
        description = row["description"]
        truncated_desc_split = description.split()
        truncated_description = ' '.join(truncated_desc_split[:30]) + "..."
        authors_split = row["authors"].split(";")
        if len(authors_split) == 2:
           authors_str = f"{authors_split[0]} and {authors_split[1]}"
        elif len(authors_split) > 2:
           authors_str = f"{authors_split[0]} et al."
        else:
            authors_str = row["authors"]
        caption = f"{row['title']} by {authors_str}: {truncated_description}"
        result.append((row["large_thumbnail"], caption))
    return result

categories = ["All"] + sorted(books["simple_categories"].unique())
tones = ["All"] + ["Happy", "Surprising", "Angry", "Suspenseful", "Sad"]

with gr.Blocks(theme=gr.themes.Glass()) as dashboard:
    gr.Markdown("# Semantic Book Recommendation System")

    with gr.Row():
        user_query = gr.Textbox(label="Please enter a description of a book:",
                                placeholder="e.g. A story about forgiveness")
        category_dropdown = gr.Dropdown(label="Select a category:", choices=categories, value="All")
        tone_dropdown = gr.Dropdown(label="Select an emotional tone:", choices=tones, value="All")
        submit_button = gr.Button("Find Recommendations")
    gr.Markdown("## Recommendations")
    output = gr.Gallery(label="Recommended Books", rows=2, columns=8)
    submit_button.click(recommend_books, inputs=[user_query, category_dropdown, tone_dropdown], outputs=output)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    dashboard.launch(server_name="0.0.0.0", server_port=port)