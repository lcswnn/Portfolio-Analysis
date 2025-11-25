#Database queries and models for Portfolio Analysis App
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Position(db.Model):
    __tablename__ = 'positions'

    id = db.Column(db.Integer, primary_key=True)
    Symbol = db.Column(db.String(50), nullable=True)
    Description = db.Column(db.String(500), nullable=True)
    Qty_Quantity = db.Column(db.String(100), nullable=True)
    Price = db.Column(db.String(100), nullable=True)
    Price_Chng_Dollar = db.Column(db.String(100), nullable=True)
    Price_Chng_Percent = db.Column(db.String(100), nullable=True)
    Mkt_Val = db.Column(db.String(100), nullable=True)
    Day_Chng_Dollar = db.Column(db.String(100), nullable=True)
    Day_Chng_Percent = db.Column(db.String(100), nullable=True)
    Cost_Basis = db.Column(db.String(100), nullable=True)
    Gain_Dollar = db.Column(db.String(100), nullable=True)
    Gain_Percent = db.Column(db.String(100), nullable=True)
    Reinvest = db.Column(db.String(50), nullable=True)
    Reinvest_Capital_Gains = db.Column(db.String(50), nullable=True)
    Security_Type = db.Column(db.String(100), nullable=True)
    Date = db.Column(db.String(50), nullable=True)