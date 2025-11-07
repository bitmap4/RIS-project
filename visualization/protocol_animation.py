import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from pathlib import Path
import imageio
import hydra
from omegaconf import DictConfig


class ProtocolVisualizer:
    def __init__(self, cfg: DictConfig):
        self.cfg = cfg
        self.output_dir = Path(cfg.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Colors from config
        self.vehicle_color = cfg.colors.vehicle
        self.fog_color = cfg.colors.fog
        self.cloud_color = cfg.colors.cloud
        self.arrow_color = cfg.colors.arrow
        self.text_color = cfg.colors.text
        self.bg_color = cfg.colors.background
        
        # Layout from config
        self.fig_width = cfg.layout.fig_width
        self.fig_height = cfg.layout.fig_height
        self.entity_width = cfg.layout.entity_width
        self.entity_height = cfg.layout.entity_height
        
        # Entity positions from config
        self.vehicle_pos = tuple(cfg.layout.vehicle_pos)
        self.fog_pos = tuple(cfg.layout.fog_pos)
        self.cloud_pos = tuple(cfg.layout.cloud_pos)
        
    def create_frame(self, frame_data: dict) -> plt.Figure:
        
        fig, ax = plt.subplots(
            figsize=(self.fig_width, self.fig_height),
            dpi=self.cfg.animation.dpi
        )
        ax.set_xlim(0, self.fig_width)
        ax.set_ylim(0, self.fig_height)
        ax.axis('off')
        fig.patch.set_facecolor(self.bg_color)
        
        # Draw entities
        self._draw_entity(ax, self.vehicle_pos, "Vehicle (V_i)", self.vehicle_color)
        self._draw_entity(ax, self.fog_pos, "Fog Node (F_j)", self.fog_color)
        self._draw_entity(ax, self.cloud_pos, "Cloud Server (CS)", self.cloud_color)
        
        # Draw frame-specific content
        if 'title' in frame_data:
            ax.text(7, 9.5, frame_data['title'], 
                   fontsize=16, fontweight='bold', ha='center')
        
        if 'actions' in frame_data:
            for action in frame_data['actions']:
                self._draw_action(ax, action)
        
        if 'arrows' in frame_data:
            for arrow in frame_data['arrows']:
                self._draw_arrow(ax, arrow)
        
        if 'checks' in frame_data:
            for check in frame_data['checks']:
                self._draw_check(ax, check)
        
        if 'keys' in frame_data:
            for key in frame_data['keys']:
                self._draw_key(ax, key)
        
        return fig
    
    def _draw_entity(self, ax, pos, label, color):
        
        rect = FancyBboxPatch(
            (pos[0] - self.entity_width/2, pos[1] - self.entity_height/2),
            self.entity_width, self.entity_height,
            boxstyle="round,pad=0.1",
            edgecolor=color, facecolor='white', linewidth=2
        )
        ax.add_patch(rect)
        ax.text(pos[0], pos[1], label, ha='center', va='center',
               fontsize=10, fontweight='bold', color=self.text_color)
    
    def _draw_action(self, ax, action):
        
        entity = action['entity']
        text = action['text']
        
        pos_map = {'vehicle': self.vehicle_pos, 'fog': self.fog_pos, 'cloud': self.cloud_pos}
        pos = pos_map[entity]
        
        y_offset = action.get('offset', -1.5)
        ax.text(pos[0], pos[1] + y_offset, text,
               ha='center', va='top', fontsize=8, 
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.8),
               wrap=True)
    
    def _draw_arrow(self, ax, arrow):
        
        from_entity = arrow['from']
        to_entity = arrow['to']
        label = arrow['label']
        
        pos_map = {'vehicle': self.vehicle_pos, 'fog': self.fog_pos, 'cloud': self.cloud_pos}
        from_pos = pos_map[from_entity]
        to_pos = pos_map[to_entity]
        
        # Determine arrow direction and calculate start/end points
        if from_pos[0] < to_pos[0]:  # Left to right
            start_x = from_pos[0] + self.entity_width/2
            end_x = to_pos[0] - self.entity_width/2
        else:  # Right to left
            start_x = from_pos[0] - self.entity_width/2
            end_x = to_pos[0] + self.entity_width/2
        
        arrow_patch = FancyArrowPatch(
            (start_x, from_pos[1]),
            (end_x, to_pos[1]),
            arrowstyle='->', mutation_scale=20, linewidth=2,
            color=self.arrow_color
        )
        ax.add_patch(arrow_patch)
        
        mid_x = (from_pos[0] + to_pos[0]) / 2
        mid_y = (from_pos[1] + to_pos[1]) / 2 + 0.3
        ax.text(mid_x, mid_y, label, ha='center', va='bottom',
               fontsize=10, fontweight='bold', color=self.arrow_color)
    
    def _draw_check(self, ax, check):
        
        entity = check['entity']
        text = check['text']
        
        pos_map = {'vehicle': self.vehicle_pos, 'fog': self.fog_pos, 'cloud': self.cloud_pos}
        pos = pos_map[entity]
        
        # Draw checkmark
        ax.text(pos[0] - 1.5, pos[1], '[+]', ha='center', va='center',
               fontsize=24, color='green', fontweight='bold')
        ax.text(pos[0] - 1.5, pos[1] - 0.5, text, ha='center', va='top',
               fontsize=7, bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.8))
    
    def _draw_key(self, ax, key):
        
        entity = key['entity']
        
        pos_map = {'vehicle': self.vehicle_pos, 'fog': self.fog_pos, 'cloud': self.cloud_pos}
        pos = pos_map[entity]
        
        # Draw key icon as a circle with "SK" text instead of emoji
        circle = plt.Circle((pos[0] + 1.5, pos[1]), 0.3, color='gold', ec='orange', linewidth=2)
        ax.add_patch(circle)
        ax.text(pos[0] + 1.5, pos[1], 'SK', ha='center', va='center',
               fontsize=8, fontweight='bold', color='black')
    
    def generate_frames(self) -> list:
        
        frames_data = [
            # Frame 1: V_i Login
            {
                'title': 'Frame 1: Vehicle Login',
                'actions': [
                    {'entity': 'vehicle', 'text': 'Computing:\nTV_i* = h(VID_i* ⊕ VPW_i* || a_i)', 'offset': -2}
                ],
                'checks': [
                    {'entity': 'vehicle', 'text': 'Login OK\nTV_i* ?= TV_i'}
                ]
            },
            
            # Frame 2: V_i -> F_j
            {
                'title': 'Frame 2: Vehicle -> Fog Node',
                'actions': [
                    {'entity': 'vehicle', 'text': 'Computing:\nM1 = {RID_i, P_i, F_i, T_1}', 'offset': -2}
                ],
                'arrows': [
                    {'from': 'vehicle', 'to': 'fog', 'label': 'M1'}
                ]
            },
            
            # Frame 3: F_j -> CS
            {
                'title': 'Frame 3: Fog Node -> Cloud Server',
                'actions': [
                    {'entity': 'fog', 'text': 'Verifying T_1\nComputing:\nM2 = {W_i, X_i, Y_i, D, T_2}', 'offset': -2.5}
                ],
                'arrows': [
                    {'from': 'fog', 'to': 'cloud', 'label': 'M2'}
                ]
            },
            
            # Frame 4: CS -> F_j
            {
                'title': 'Frame 4: Cloud Server -> Fog Node',
                'actions': [
                    {'entity': 'cloud', 'text': 'Verifying T_2\nComputing SK\nM3 = {L_i, Z_i, T_3}', 'offset': -2.5}
                ],
                'checks': [
                    {'entity': 'cloud', 'text': 'Auth V_i, F_j OK\nD* ?= D'}
                ],
                'keys': [
                    {'entity': 'cloud'}
                ],
                'arrows': [
                    {'from': 'cloud', 'to': 'fog', 'label': 'M3'}
                ]
            },
            
            # Frame 5: F_j -> V_i
            {
                'title': 'Frame 5: Fog Node -> Vehicle',
                'actions': [
                    {'entity': 'fog', 'text': 'Verifying T_3\nComputing SK*\nM4 = {N_i, J_i, T_4}', 'offset': -2.5}
                ],
                'checks': [
                    {'entity': 'fog', 'text': 'Auth CS OK\nZ_i* ?= Z_i'}
                ],
                'keys': [
                    {'entity': 'fog'},
                    {'entity': 'cloud'}
                ],
                'arrows': [
                    {'from': 'fog', 'to': 'vehicle', 'label': 'M4'}
                ]
            },
            
            # Frame 6: Session Established
            {
                'title': 'Frame 6: Session Established',
                'actions': [
                    {'entity': 'vehicle', 'text': 'Verifying T_4\nComputing SK', 'offset': -2}
                ],
                'checks': [
                    {'entity': 'vehicle', 'text': 'Auth F_j OK\nJ_i* ?= J_i'}
                ],
                'keys': [
                    {'entity': 'vehicle'},
                    {'entity': 'fog'},
                    {'entity': 'cloud'}
                ]
            }
        ]
        
        return frames_data
    
    def create_gif(self):
        
        print("Generating protocol visualization frames...")
        
        frames_data = self.generate_frames()
        frame_files = []
        
        for i, frame_data in enumerate(frames_data):
            print(f"  Creating frame {i+1}/{len(frames_data)}...")
            fig = self.create_frame(frame_data)
            
            frame_path = self.output_dir / f"frame_{i:02d}.png"
            fig.savefig(
                frame_path,
                dpi=self.cfg.animation.dpi,
                bbox_inches=None,
                facecolor=self.bg_color,
                pad_inches=0.1
            )
            frame_files.append(frame_path)
            plt.close(fig)
        
        # Create GIF
        print("Creating animated GIF...")
        gif_path = self.output_dir / "protocol_flow.gif"
        
        images = []
        for frame_file in frame_files:
            images.append(imageio.imread(frame_file))
        
        # Save with duration from config (in milliseconds)
        imageio.mimsave(
            gif_path,
            images,
            duration=self.cfg.animation.duration,
            loop=self.cfg.animation.loop
        )
        
        print(f"\n[+] Animated GIF saved to: {gif_path}")
        print(f"[+] Individual frames saved to: {self.output_dir}")
        return gif_path


@hydra.main(version_base=None, config_path="configs", config_name="config")
def main(cfg: DictConfig):
    
    visualizer = ProtocolVisualizer(cfg)
    visualizer.create_gif()


if __name__ == "__main__":
    main()
