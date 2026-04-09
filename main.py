import src.config as config
from src.graph_manager import GraphManager
from src.rag_engine import RAGEngine
from src.monitor import DissatisfactionMonitor
import sys

def main():
    print("Initializing NeuroGraph System...")
    
    # Init Components
    try:
        gm = GraphManager()
        # Test connection
        gm.query("RETURN 1")
        print(" Connected to Neo4j.")
    except Exception as e:
        print(f"Neo4j Connection Failed: {e}")
        print("Please check your Neo4j container/app is running and credentials in src/config.py are correct.")
        sys.exit(1)

    rag = RAGEngine(gm)
    monitor = DissatisfactionMonitor()
    
    history = []
    
    print("\nSystem Ready. (Type 'exit' to quit)")
    print("------------------------------------------------")
    
    last_bot_reply = ""
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            # Analyze previous interaction for potential dissatisfaction *before* processing new turn?
            # Or analyze *after* the user complains about the *last* reply?
            # The prompt structure I built in monitor.py expects (User Input + Last Bot Reply).
            # So if I said "X", and User says "That's wrong", monitor checks ("That's wrong", "X").
            
            if last_bot_reply:
                is_dissatisfied, reason = monitor.analyze_interaction(user_input, last_bot_reply, history[-3:])
                if is_dissatisfied:
                    print(f"   [Observation]: You seem dissatisfied with my last answer. Reason: {reason}")
                    print(f"   [System]: Logged for training.")

            # Generate new reply
            print("Thinking...", end="\r")
            bot_reply = rag.generate_reply(user_input)
            print(" " * 20, end="\r") # Clear 'Thinking...'
            
            print(f"Bot: {bot_reply}")
            
            # Update history
            history.append(f"User: {user_input}")
            history.append(f"Bot: {bot_reply}")
            last_bot_reply = bot_reply

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            break

    gm.close()

if __name__ == "__main__":
    main()
