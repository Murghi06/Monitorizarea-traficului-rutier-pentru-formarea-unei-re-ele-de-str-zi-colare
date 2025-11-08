"""
Vehicle tracking module
Handles object tracking and counting
"""

import numpy as np
from collections import defaultdict
from config.constants import (
    DISTANCE_THRESHOLD, MAX_DISAPPEARED_FRAMES, PARKED_THRESHOLD, 
    MOVEMENT_THRESHOLD, SKIP_FRAMES
)


class VehicleTracker:
    """Tracks vehicles across frames"""
    
    def __init__(self):
        self.tracked_objects = {}
        self.next_object_id = 0
        self.vehicle_counts = defaultdict(int)
        
        # Adjust tracking parameters based on frame skipping
        # When skipping frames, we need to be more tolerant of "disappeared" objects
        self.max_disappeared = MAX_DISAPPEARED_FRAMES // SKIP_FRAMES
        # Also increase distance threshold slightly when skipping frames
        self.distance_threshold = DISTANCE_THRESHOLD * (1 + (SKIP_FRAMES - 1) * 0.2)
        self.movement_threshold = MOVEMENT_THRESHOLD
        
    def set_scaled_parameters(self, distance_threshold, movement_threshold):
        """Update tracking thresholds based on video resolution"""
        self.distance_threshold = distance_threshold * (1 + (SKIP_FRAMES - 1) * 0.2)
        self.movement_threshold = movement_threshold
        
    def reset(self):
        """Reset tracker state"""
        self.tracked_objects = {}
        self.next_object_id = 0
        self.vehicle_counts = defaultdict(int)
    
    @staticmethod
    def calculate_centroid(box):
        """Calculate center point of bounding box"""
        x1, y1, x2, y2 = box
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))
    
    @staticmethod
    def calculate_distance(p1, p2):
        """Calculate Euclidean distance between two points"""
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        return (dx * dx + dy * dy) ** 0.5
    
    def update(self, detections):
        """
        Update tracking with new detections
        Returns list of newly registered object IDs
        """
        if not detections:
            # Mark all objects as disappeared
            for obj_id in list(self.tracked_objects.keys()):
                self.tracked_objects[obj_id]['disappeared'] += 1
                if self.tracked_objects[obj_id]['disappeared'] > self.max_disappeared:
                    del self.tracked_objects[obj_id]
            return []
        
        current_centroids = [self.calculate_centroid(det['box']) for det in detections]
        
        if not self.tracked_objects:
            return self._register_new_objects(detections, current_centroids)
        
        return self._match_and_update(detections, current_centroids)
    
    def _register_new_objects(self, detections, centroids):
        """Register completely new objects - don't count until movement is confirmed"""
        new_objects = []
        for i, det in enumerate(detections):
            self.tracked_objects[self.next_object_id] = {
                'centroid': centroids[i],
                'disappeared': 0,
                'class': det['class'],
                'counted': False,
                'stationary_frames': 0,
                'is_parked': False,
                'total_movement': 0,
                'has_moved': False  # NEW: Track if vehicle has ever moved
            }
            new_objects.append(self.next_object_id)
            self.next_object_id += 1
        return new_objects
    
    def _match_and_update(self, detections, current_centroids):
        """Match current detections to tracked objects"""
        object_ids = list(self.tracked_objects.keys())
        object_centroids = [self.tracked_objects[oid]['centroid'] for oid in object_ids]
        
        # Calculate distance matrix
        obj_array = np.array(object_centroids)
        curr_array = np.array(current_centroids)
        
        distances = np.zeros((len(object_centroids), len(current_centroids)))
        for i in range(len(obj_array)):
            distances[i] = np.sqrt(np.sum((curr_array - obj_array[i])**2, axis=1))
        
        matched_objects = set()
        matched_detections = set()
        new_objects = []
        
        # Match closest pairs
        for _ in range(min(len(object_ids), len(current_centroids))):
            min_idx = np.unravel_index(distances.argmin(), distances.shape)
            
            if distances[min_idx] < self.distance_threshold:
                obj_id = object_ids[min_idx[0]]
                obj = self.tracked_objects[obj_id]
                old_centroid = obj['centroid']
                new_centroid = current_centroids[min_idx[1]]
                
                movement = self.calculate_distance(old_centroid, new_centroid)
                
                # Update object
                obj['centroid'] = new_centroid
                obj['disappeared'] = 0
                obj['total_movement'] += movement
                
                # Track stationary frames
                if movement < self.movement_threshold:
                    obj['stationary_frames'] += 1
                else:
                    # Vehicle is moving
                    obj['stationary_frames'] = 0
                    obj['is_parked'] = False
                    
                    # Mark that this vehicle has moved at least once
                    if not obj['has_moved']:
                        obj['has_moved'] = True
                        # Count vehicle now that it has shown movement
                        if not obj['counted']:
                            self.vehicle_counts[obj['class']] += 1
                            obj['counted'] = True
                            print(f"✓ Counted {obj['class']} after movement (ID: {obj_id}) - Total {obj['class']}: {self.vehicle_counts[obj['class']]}")
                
                # Mark as parked if stationary for very long
                if obj['stationary_frames'] > PARKED_THRESHOLD:
                    obj['is_parked'] = True
                
                matched_objects.add(min_idx[0])
                matched_detections.add(min_idx[1])
                distances[min_idx[0], :] = np.inf
                distances[:, min_idx[1]] = np.inf
        
        # Handle unmatched objects (disappeared)
        for i, obj_id in enumerate(object_ids):
            if i not in matched_objects:
                self.tracked_objects[obj_id]['disappeared'] += 1
                if self.tracked_objects[obj_id]['disappeared'] > self.max_disappeared:
                    del self.tracked_objects[obj_id]
        
        # Handle unmatched detections (new objects)
        for i in range(len(current_centroids)):
            if i not in matched_detections:
                # Check if it's a rediscovered object
                is_rediscovery = False
                for obj_id, obj in list(self.tracked_objects.items()):
                    if obj['disappeared'] > 0 and obj['disappeared'] <= self.max_disappeared:
                        distance = self.calculate_distance(obj['centroid'], current_centroids[i])
                        if distance < self.distance_threshold * 1.5:
                            obj['centroid'] = current_centroids[i]
                            obj['disappeared'] = 0
                            is_rediscovery = True
                            break
                
                if not is_rediscovery:
                    self.tracked_objects[self.next_object_id] = {
                        'centroid': current_centroids[i],
                        'disappeared': 0,
                        'class': detections[i]['class'],
                        'counted': False,
                        'stationary_frames': 0,
                        'is_parked': False,
                        'total_movement': 0,
                        'has_moved': False  # NEW: Track if vehicle has ever moved
                    }
                    new_objects.append(self.next_object_id)
                    self.next_object_id += 1
        
        return new_objects
    
    def count_new_vehicles(self, new_object_ids):
        """
        Don't count vehicles immediately upon detection.
        Vehicles are only counted when they show movement (handled in _match_and_update).
        This prevents parked cars from being counted.
        """
        # This method is now primarily a placeholder for the interface
        # Actual counting happens in _match_and_update when movement is detected
        pass
    
    def is_object_parked(self, centroid):
        """Check if a detection corresponds to a parked object"""
        for obj in self.tracked_objects.values():
            if self.calculate_distance(obj['centroid'], centroid) < 50:
                return obj['is_parked']
        return False
    
    def get_counts(self):
        """Get current vehicle counts"""
        return dict(self.vehicle_counts)
    
    def get_total_count(self):
        """Get total vehicle count"""
        return sum(self.vehicle_counts.values())
