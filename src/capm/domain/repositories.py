from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.capm.config import settings

Base = declarative_base()


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False, index=True)
    market_ticker = Column(String, nullable=False)
    current_price = Column(Float, nullable=True)
    volume = Column(Integer, nullable=True)
    beta = Column(Float, nullable=False)
    alpha = Column(Float, nullable=False)
    capm = Column(Float, nullable=False)
    sharpe = Column(Float, nullable=False)
    r_squared = Column(Float, nullable=False)
    p_value = Column(Float, nullable=False)
    std_error = Column(Float, nullable=False)
    risk_free_rate = Column(Float, nullable=False)
    risk_free_source = Column(String, nullable=True)
    market_return = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True, nullable=False)


class SQLiteMetricRepository:
    def __init__(self):
        self.engine = create_engine(f"sqlite:///{settings.db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def upsert_metrics(self, metrics: list[dict]) -> None:
        with self.Session() as session:
            for m in metrics:
                existing = (
                    session.query(Metric).filter(Metric.ticker == m["ticker"]).first()
                )
                if existing:
                    for key, value in m.items():
                        setattr(existing, key, value)
                    existing.active = True
                else:
                    session.add(Metric(**m))
            session.commit()

    def get_all_metrics(self, active_only: bool = True) -> list[Metric]:
        with self.Session() as session:
            query = session.query(Metric)
            if active_only:
                query = query.filter(Metric.active == True)
            return query.order_by(Metric.calculated_at.desc()).all()

    def get_metric_by_ticker(self, ticker: str) -> Metric | None:
        with self.Session() as session:
            return session.query(Metric).filter(Metric.ticker == ticker.upper()).first()

    def get_latest_calculation(self) -> Metric | None:
        with self.Session() as session:
            return session.query(Metric).order_by(Metric.calculated_at.desc()).first()

    def get_active_tickers(self) -> list[str]:
        with self.Session() as session:
            return [
                m.ticker
                for m in session.query(Metric.ticker)
                .filter(Metric.active == True)
                .all()
            ]

    def toggle_active(self, ticker: str, active: bool) -> bool:
        with self.Session() as session:
            metric = (
                session.query(Metric).filter(Metric.ticker == ticker.upper()).first()
            )
            if metric:
                metric.active = active
                session.commit()
                return True
            return False

    def delete_metric(self, ticker: str) -> bool:
        with self.Session() as session:
            metric = (
                session.query(Metric).filter(Metric.ticker == ticker.upper()).first()
            )
            if metric:
                session.delete(metric)
                session.commit()
                return True
            return False


DatabaseManager = SQLiteMetricRepository
