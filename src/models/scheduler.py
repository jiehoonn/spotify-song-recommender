import schedule
import time
import threading
from datetime import datetime
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.models.active_learner import active_learner

class ModelScheduler:
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        
    def retrain_job(self):
        """Periodic retraining job"""
        try:
            print(f"[{datetime.now()}] Checking if model needs retraining...")
            
            # Load existing model if not loaded
            if not active_learner.is_trained:
                active_learner.load_model()
            
            feedback_count = active_learner.get_feedback_count()
            feedback_stats = active_learner.get_feedback_stats()
            
            print(f"Feedback stats: {feedback_stats}")
            
            # Retrain if we have enough feedback
            if feedback_count >= active_learner.min_training_samples:
                print(f"Found {feedback_count} feedback samples. Retraining model...")
                
                success = active_learner.train_model()
                if success:
                    active_learner.save_model()
                    print("✅ Model retrained and saved successfully!")
                    
                    # Print latest training metrics
                    if active_learner.training_history:
                        latest = active_learner.training_history[-1]
                        print(f"Latest model metrics: Accuracy={latest['accuracy']:.3f}, F1={latest['f1']:.3f}")
                else:
                    print("❌ Model retraining failed")
            else:
                print(f"Not enough feedback ({feedback_count}/{active_learner.min_training_samples}). Skipping retraining.")
                
        except Exception as e:
            print(f"Error in retraining job: {e}")
            import traceback
            traceback.print_exc()
    
    def run_scheduler(self):
        """Run the scheduler in background"""
        # Schedule retraining every day at 2 AM
        schedule.every().day.at("02:00").do(self.retrain_job)
        
        # Also check for retraining every 6 hours
        schedule.every(6).hours.do(self.retrain_job)
        
        print(f"[{datetime.now()}] Scheduler started. Retraining at 2 AM daily and every 6 hours.")
        
        self.is_running = True
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start_scheduler(self):
        """Start scheduler in a background thread"""
        if self.scheduler_thread is None or not self.scheduler_thread.is_alive():
            self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.scheduler_thread.start()
            print("Background scheduler started")
            return self.scheduler_thread
        else:
            print("Scheduler already running")
            return self.scheduler_thread
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            print("Scheduler stopped")

# Global instance
model_scheduler = ModelScheduler()

# For production deployment
if __name__ == "__main__":
    print("Starting model scheduler...")
    model_scheduler.start_scheduler()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Shutting down scheduler...")
        model_scheduler.stop_scheduler()
