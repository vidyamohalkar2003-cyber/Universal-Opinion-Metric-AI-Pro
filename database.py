import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "2003")
DB_PORT = os.getenv("DB_PORT", "5432") 


DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)

def save_records_to_postgres(df, query_term):
    """Inserts processed analytics into PostgreSQL using secure connection pooling."""
    if df.empty:
        return 0
        
    inserted_counter = 0
    with engine.begin() as connection:
        for _, row in df.iterrows():
            try:
                check_query = text("SELECT 1 FROM public_opinions WHERE response_id = :res_id")
                exists = connection.execute(check_query, {"res_id": row['Response_ID']}).fetchone()
                
                if not exists:
                    insert_query = text("""
                        INSERT INTO public_opinions (
                            search_query, response_id, timestamp_raw, feedback_date, 
                            channel, region, customer_feedback, polarity, subjectivity, sentiment_category
                        ) VALUES (:q, :res_id, :ts, :dt, :ch, :reg, :fb, :pol, :sub, :cat)
                    """)
                    connection.execute(insert_query, {
                        "q": query_term, "res_id": row['Response_ID'], "ts": str(row['Timestamp']),
                        "dt": row['Date'], "ch": row['Channel'], "reg": row['Region'],
                        "fb": row['Customer_Feedback'], "pol": float(row['Polarity']),
                        "sub": float(row['Subjectivity']), "cat": str(row['Sentiment_Category'])
                    })
                    inserted_counter += 1
            except Exception:
                continue
                
    return inserted_counter
