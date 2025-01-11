# File: apifuncs.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import select, and_, not_
from sqlalchemy import select, func, Table, Column, Integer, String, MetaData,Date,Enum,ForeignKey, create_engine
from sqlalchemy.sql import select, insert, update, delete
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy import delete, select
from sqlalchemy.exc import NoResultFound
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import cast, String
from sqlalchemy import Table, update
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from sqlalchemy.exc import IntegrityError
#from browsing import browse
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from url_utils import standardize_url 
import requests
import google.generativeai as genai
import re

# Database connection
engine = create_engine('postgresql://pguser:pgpass@pghost:5432/dbname')
metadata = MetaData()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()


genai.configure(api_key="my-api-key")
model = genai.GenerativeModel("gemini-1.5-flash")
POLICY = 'strict'  # or 'lenient'


# Define the tables
pages   = Table('page', metadata, autoload_with=engine)
page_content   = Table('page_content', metadata, autoload_with=engine)

class Page_FUNCS:
    @staticmethod
    def get_medium_content_Scores(url):
        try:
            with engine.connect() as connection:
                # Fetch content from Medium
                response = requests.get(url)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                soup = BeautifulSoup(response.content, "html.parser")

                # Extract title
                title_element = soup.find("h1", class_=lambda x: x and "pw-post-title" in x)
                title = title_element.text.strip() if title_element else "Title not found"

                # Extract paragraphs
                paragraph_elements = soup.find_all("p", class_=lambda x: x and "pw-post-body-paragraph" in x)
                paragraphs = [p.text.strip() for p in paragraph_elements]

                # Calculate content hash (optional)
                all_content = "\n".join(paragraphs)  # Join paragraphs with newline characters
                page_content_hash = hash(all_content.encode('utf-8'))
                url_query = connection.execute(select(pages.c.url).where(pages.c.url == url))
                page_result = url_query.fetchall()
                if len(page_result) > 0 :
                    result = connection.execute(
                        select(
                            pages.c.violence_score, 
                            pages.c.age_restriction_score, 
                            pages.c.spamicity_score)
                        .where(pages.c.url == url)
                    )
                    scores = result.fetchall()
                    return [dict(row._mapping) for row in scores]

                else:                
                    page_data = {"url": url}  
                    if page_content_hash:  
                        page_data["page_content_hash"] = page_content_hash                
                    page_data["page-title"] = title                
                    stmt = insert(pages).values(page_data).returning(pages.c.id)
                    result = connection.execute(stmt)
                    page_id = result.scalar()

                    # Insert each paragraph as a separate record
                    for idx, paragraph in enumerate(paragraphs):
                        response = model.generate_content(f""""Act as an intelligent language model that must evaluate the following
                                                    text on two metrics—Age Restriction and Violence—each on a 1–100 scale 
                                                    (1=lowest, 10=highest); provide the results in the format 'Age Restriction: X';'Violence: Y';
                                                          the evaluation policy is {POLICY} 
                                                    ('strict' = lean towards higher scores in ambiguous cases, 'lenient' = lean towards lower scores); 
                                                    here is the text: {paragraph}.""")
                        
                        match = re.match(r"Age Restriction: (\d+); Violence: (\d+);", response.text)
                        age_restriction = int(match.group(1))
                        violence = int(match.group(2))                        
                        text_type = 1  # Assuming 1 for paragraphs
                        sequence_number = idx + 1
                        content_hash = hash(paragraph)  # Individual paragraph hash
                        stmt = insert(page_content).values(
                            page_id=page_id,
                            text_type=text_type,
                            text_content=paragraph,
                            content_hash=content_hash,
                            sequence_number=sequence_number,
                            age_restriction_score = age_restriction,
                            violence_score = violence
                        )
                        connection.execute(stmt)

                    connection.commit()
                    return page_id

        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Error fetching URL: {e}")
        except AttributeError as e:  # Handle cases where elements are not found
            raise HTTPException(status_code=500, detail=f"Error parsing content: {e}. Element not found.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    @staticmethod
    def get_page_scores(url):
        try:
            with engine.connect() as connection:
                stmt = select(pages).where(pages.c.url == url)
                existing_page = connection.execute(stmt).fetchone()

                if existing_page:
                    page_id = existing_page.id
                    page_age_restriction_score = existing_page.age_restriction_score
                    page_violence_score = existing_page.violence_score
                    spamicity_score = existing_page.spamicity_score

                    content_scores_query = connection.execute(
                        select(page_content.c.age_restriction_score, page_content.c.violence_score)
                        .where(page_content.c.page_id == page_id)
                    )
                    content_scores = content_scores_query.fetchall()
                    content_scores = [(score[0], score[1]) for score in content_scores]

                    return {
                        "page_age_restriction_score": page_age_restriction_score,
                        "page_violence_score": page_violence_score,
                        "spamicity_score": spamicity_score,
                        "content_scores": content_scores,
                    }
                else:
                    return None  # URL not found

        except Exception as e:
            print(f"An unexpected error occurred: {e}") #Print the exception to the console for debugging
            return None