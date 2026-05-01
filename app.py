import os
import logging
from flask import Flask, render_template, request, jsonify

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-in-render")

# Decision thresholds
APPROVE_SCORE_THRESHOLD = 80
CONDITIONAL_SCORE_THRESHOLD = 60
REJECT_SCORE_THRESHOLD = 60

def calculate_credit_score(income, loan_amount, credit_history=50):
    """Calculate credit score based on income, loan amount, and history"""
    try:
        # Debt-to-income ratio (lower is better)
        debt_ratio = (loan_amount / (income * 12)) * 100 if income > 0 else 100
        
        # Score calculation (0-100)
        score = 100
        
        # Deduct for high debt ratio
        if debt_ratio > 50:
            score -= 30
        elif debt_ratio > 40:
            score -= 20
        elif debt_ratio > 30:
            score -= 10
        
        # Factor in credit history
        score = (score * 0.7) + (credit_history * 0.3)
        
        return max(0, min(100, score))
    except:
        return 50

def make_decision(credit_score, default_probability=30):
    """Make loan decision based on credit score and default probability"""
    logger.debug(f"Making decision: score={credit_score}, default={default_probability}%")
    
    # High risk - reject
    if default_probability > 50:
        return {
            "decision": "REJECT",
            "reason": f"High default probability ({default_probability}%)",
            "color": "reject"
        }
    
    # Good score - approve
    if credit_score >= APPROVE_SCORE_THRESHOLD:
        return {
            "decision": "APPROVE",
            "reason": f"Excellent credit score ({credit_score})",
            "color": "approve"
        }
    
    # Medium score - conditional
    if credit_score >= CONDITIONAL_SCORE_THRESHOLD:
        return {
            "decision": "CONDITIONAL APPROVE",
            "reason": f"Good credit score ({credit_score}) with monitoring required",
            "color": "conditional"
        }
    
    # Low score - reject
    return {
        "decision": "REJECT",
        "reason": f"Low credit score ({credit_score})",
        "color": "reject"
    }

@app.route("/", methods=["GET"])
def index():
    """Render the application form"""
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    """Process loan application"""
    try:
        logger.debug(f"Received POST request with form data: {request.form}")
        
        # Get form data
        borrower_name = request.form.get("borrower_name", "").strip()
        income = request.form.get("income", "0")
        loan_amount = request.form.get("loan_amount", "0")
        credit_history = request.form.get("credit_history", "50")
        
        # Validate required fields
        if not borrower_name:
            logger.warning("Borrower name is empty")
            return render_template(
                "index.html",
                error="Please enter borrower name",
                borrower_name=borrower_name,
                income=income,
                loan_amount=loan_amount,
            ), 400
        
        try:
            income = float(income)
            loan_amount = float(loan_amount)
            credit_history = float(credit_history)
        except ValueError:
            logger.error("Invalid numeric values provided")
            return render_template(
                "index.html",
                error="Please enter valid numeric values",
                borrower_name=borrower_name,
                income=income,
                loan_amount=loan_amount,
            ), 400
        
        # Validate numeric ranges
        if income <= 0 or loan_amount <= 0:
            logger.warning(f"Invalid income or loan amount: income={income}, loan={loan_amount}")
            return render_template(
                "index.html",
                error="Income and loan amount must be greater than 0",
                borrower_name=borrower_name,
                income=income,
                loan_amount=loan_amount,
            ), 400
        
        # Calculate credit score
        credit_score = calculate_credit_score(income, loan_amount, credit_history)
        logger.info(f"Calculated credit score: {credit_score}")
        
        # Calculate default probability
        debt_ratio = (loan_amount / (income * 12)) * 100
        default_probability = min(100, max(10, debt_ratio * 0.5))
        logger.info(f"Default probability: {default_probability}%")
        
        # Make decision
        result = make_decision(credit_score, default_probability)
        logger.info(f"Decision made: {result['decision']}")
        
        # Add extra info to result
        result.update({
            "borrower_name": borrower_name,
            "credit_score": round(credit_score, 2),
            "default_probability": round(default_probability, 2),
            "debt_ratio": round(debt_ratio, 2),
            "income": income,
            "loan_amount": loan_amount,
        })
        
        return render_template(
            "index.html",
            result=result,
            borrower_name=borrower_name,
            income=income,
            loan_amount=loan_amount,
        ), 200

    except Exception as e:
        logger.error(f"Error processing application: {str(e)}", exc_info=True)
        return render_template(
            "index.html",
            error=f"An error occurred: {str(e)}",
        ), 500

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "app": "Climate Credit Flask App"}), 200

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 error: {request.path}")
    return render_template("index.html", error="Page not found"), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {error}", exc_info=True)
    return render_template("index.html", error="Server error occurred"), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
