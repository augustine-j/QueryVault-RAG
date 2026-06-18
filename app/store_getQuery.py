from app.database import SessionLocal
from app.models.query_log import QueryLog
from sqlalchemy.orm import Session
from sqlalchemy import func
    


def save_query(
        db:Session,
        question:str,
        answer:str,
        response_time:float,
        answer_found:int,):
    
    query = QueryLog(
        question=question,
        answer=answer,
        response_time=response_time,
        answer_found=answer_found
    )

    db.add(query)
    db.commit()
    db.refresh(query)

    return query



    
    
def get_analytics(db):
    total_queries= db.query(QueryLog).count()

    avg_response_time = db.query(func.avg(QueryLog.response_time)).scalar()
    successful_answers = db.query(QueryLog).filter(QueryLog.answer_found == 1).count()
    failed_answers = db.query(QueryLog).filter(QueryLog.answer_found == 0).count()
    success_rate = round((successful_answers / total_queries) * 100,2)

    top_questions = (db.query(
        QueryLog.question,
        func.count(QueryLog.question).label("count")
    )
    .group_by(QueryLog.question)
    .order_by(func.count(QueryLog.question).desc())
    .limit(5)
    .distinct()
    .all()
    )

    top_questions_data = [
    {
        "question": question,
        "count": count
    }
    for question, count in top_questions
    ]

    failed_queries = (db.query(QueryLog.question).filter(QueryLog.answer_found == 0).distinct().all())
    failed_queries_data = [question for (question,) in failed_queries]
    
    

    return{
        "total_queries": total_queries,
        "avarage_response_time":round(avg_response_time or 0,2),
        "successful_answers":successful_answers,
        "failed_answers":failed_answers,
        "sucess_rate":success_rate,
        "top_questions":top_questions_data,
        "failed_queries":failed_queries_data,



    }
    


