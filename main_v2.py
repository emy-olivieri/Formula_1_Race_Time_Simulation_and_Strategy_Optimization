######
# Input : "Saison", "Course", "Pit_Stop_Strategy"
from Run import run

if __name__ == "__main__":
    try:
        Run = Run("Saison", "Course", "Pit_Stop_Strategy -> Dictionnaire qui donne pour chaque driver sa strategy pitstop {'Hamilton' : '{'15' : 'Medium', '28' : 'Hard'}'}")
        Run.run()
        
    except Exception as e:
        print(f"[ERROR] An exception occurred: {e}")