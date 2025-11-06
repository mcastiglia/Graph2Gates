import time


class TrainingTimer:
    def __init__(self, num_episodes: int, num_steps: int, step_window_size: int = 10, episode_window_size: int = 5):
        self.num_episodes = num_episodes
        self.num_steps = num_steps
        self.step_window_size = min(step_window_size, num_steps)
        self.episode_window_size = episode_window_size
        
        self.step_times = []
        self.episode_times = []
        self.episode_init_times = []
        self.total_start_time = time.time()
        
        self.episode_start_time = None
        self.init_start_time = None
        self.step_start_time = None
    
    def start_episode(self, episode_num: int):
        self.episode_start_time = time.time()
        self.episode_num = episode_num
    
    def start_init(self):
        self.init_start_time = time.time()
    
    def end_init(self):
        if self.init_start_time is None:
            return 0.0
        init_time = time.time() - self.init_start_time
        self.episode_init_times.append(init_time)
        if len(self.episode_init_times) > self.episode_window_size:
            self.episode_init_times.pop(0)
        return init_time
    
    def start_step(self):
        self.step_start_time = time.time()
    
    def end_step(self, step: int, pbar=None):
        if self.step_start_time is None:
            return None
        
        step_time = time.time() - self.step_start_time
        self.step_times.append(step_time)
        if len(self.step_times) > self.step_window_size:
            self.step_times.pop(0)
        
        if pbar is not None and len(self.step_times) > 0:
            avg_step_time = sum(self.step_times) / len(self.step_times)
            remaining_steps = self.num_steps - step - 1
            eta_seconds = avg_step_time * remaining_steps
            eta_minutes = eta_seconds / 60
            
            pbar.set_postfix({
                'step_time': f'{step_time:.2f}s',
                'avg_time': f'{avg_step_time:.2f}s',
                'eta': f'{eta_minutes:.1f}m'
            })
        
        self.step_start_time = time.time()
        return step_time
    
    def end_episode(self, init_time: float):
        if self.episode_start_time is None:
            return None, None
        
        episode_time = time.time() - self.episode_start_time
        self.episode_times.append(episode_time)
        if len(self.episode_times) > self.episode_window_size:
            self.episode_times.pop(0)
        
        avg_episode_time = sum(self.episode_times) / len(self.episode_times) if self.episode_times else episode_time
        avg_init_time = sum(self.episode_init_times) / len(self.episode_init_times) if self.episode_init_times else init_time
        remaining_episodes = self.num_episodes - self.episode_num - 1
        total_eta_seconds = (avg_episode_time + avg_init_time) * remaining_episodes
        total_eta_hours = total_eta_seconds / 3600
        
        elapsed_time = time.time() - self.total_start_time
        elapsed_hours = elapsed_time / 3600
        
        return episode_time, {
            'avg_episode_time': avg_episode_time,
            'avg_init_time': avg_init_time,
            'remaining_episodes': remaining_episodes,
            'total_eta_seconds': total_eta_seconds,
            'total_eta_hours': total_eta_hours,
            'elapsed_hours': elapsed_hours
        }
    
    def print_episode_summary(self, episode_num: int, episode_time: float, init_time: float, estimates: dict):
        print(f"\nEpisode {episode_num+1} completed in {episode_time:.1f}s (init: {init_time:.1f}s, steps: {episode_time-init_time:.1f}s)")
        if estimates['remaining_episodes'] > 0:
            print(f"Estimated remaining: {estimates['total_eta_hours']:.2f}h ({estimates['total_eta_seconds']/60:.1f}m) | Elapsed: {estimates['elapsed_hours']:.2f}h")
    
    def print_final_summary(self):
        total_time = time.time() - self.total_start_time
        total_hours = total_time / 3600
        avg_episode_time = sum(self.episode_times) / len(self.episode_times) if self.episode_times else 0
        avg_step_time = sum(self.step_times) / len(self.step_times) if self.step_times else 0
        
        print(f"\n{'='*60}")
        print(f"Training completed!")
        print(f"Total time: {total_hours:.2f}h ({total_time/60:.1f}m)")
        print(f"Average episode time: {avg_episode_time:.1f}s")
        print(f"Average step time: {avg_step_time:.2f}s")
        print(f"Total episodes: {self.num_episodes}")
        print(f"Total steps: {self.num_episodes * self.num_steps}")
        print(f"{'='*60}\n")

