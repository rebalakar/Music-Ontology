import sys
import os
import cProfile
import pstats

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from src.main import main 

def profile_main():
    profiler = cProfile.Profile()
    profiler.enable()  
    main()            
    profiler.disable() 
    
    # Create a Stats object sorted by cumulative time (slowest functions first)
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(20)

if __name__ == "__main__":
    profile_main()