from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from database import MacroIndicator

class MacroIndicatorRepository:
    def __init__(self, db): self.db = db

    def latest_valid(self):
        return (self.db.query(MacroIndicator)
                .filter(MacroIndicator.extraction_status == "validated")
                .order_by(desc(MacroIndicator.reference_date),
                          desc(MacroIndicator.publication_date),
                          desc(MacroIndicator.created_at)).first())

    def valid_history(self, earliest_date=None):
        query = self.db.query(MacroIndicator).filter(MacroIndicator.extraction_status == "validated")
        if earliest_date is not None: query = query.filter(MacroIndicator.reference_date >= earliest_date)
        return query.order_by(MacroIndicator.reference_date).all()

    def checksum_exists(self, checksum):
        return self.db.query(MacroIndicator.id).filter(MacroIndicator.source_checksum == checksum).first() is not None

    def insert(self, record):
        try:
            self.db.add(record); self.db.commit(); self.db.refresh(record); return record
        except IntegrityError:
            self.db.rollback(); return None
