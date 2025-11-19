"""
Gemini API Integration for Rememory
Processes GPS, audio, and photo data to generate contextual state
"""

import google.generativeai as genai
from datetime import datetime
import os
from typing import Dict, List, Any
import json


class GeminiProcessor:
    """Handles all Gemini API interactions for state generation"""

    def __init__(self, api_key: str):
        """Initialize Gemini API client"""
        if not api_key:
            raise ValueError("Gemini API key is required")

        genai.configure(api_key=api_key)
        # Using Gemini 3.0 Pro (released November 2025)
        try:
            self.model = genai.GenerativeModel('gemini-3-pro-preview-11-2025')
        except Exception as e:
            print(f"[Gemini] Warning: Could not load Gemini 3 Pro, trying fallback: {str(e)}")
            try:
                # Fallback to Gemini 2.0 Flash
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            except Exception:
                # Final fallback to stable model
                self.model = genai.GenerativeModel('gemini-1.5-pro')

        print(f"[Gemini] Initialized with model: {self.model.model_name}")

        # Context accumulator for maintaining conversation history
        self.context_history = []

    def generate_state(self, data: Dict[str, Any]) -> str:
        """
        Generate current state summary from collected data

        Args:
            data: Dictionary containing:
                - gps_data: List of GPS coordinates
                - photos: List of photo metadata
                - audio_chunks: Number of audio chunks

        Returns:
            String describing current state and context
        """
        try:
            # Build prompt from collected data
            prompt = self._build_state_prompt(data)

            # Generate response from Gemini
            response = self.model.generate_content(prompt)

            # Extract text from response
            state_text = response.text

            # Add to context history (keep last 10 interactions)
            self.context_history.append({
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt[:200] + '...',  # Truncate for storage
                'response': state_text
            })
            if len(self.context_history) > 10:
                self.context_history = self.context_history[-10:]

            return state_text

        except Exception as e:
            error_msg = f"Unable to generate state: {str(e)}"
            print(f"[Gemini Error] {error_msg}")
            return error_msg

    def _build_state_prompt(self, data: Dict[str, Any]) -> str:
        """Build comprehensive prompt for Gemini from all available data"""

        prompt_parts = []

        # System context
        prompt_parts.append("""You are an AI assistant helping someone with memory difficulties.
Your job is to analyze their current location, surroundings, and activities to provide a clear,
concise summary of where they are and what's happening around them.

Be reassuring, specific, and helpful. Focus on:
1. Current location and what's at that location
2. What activity they appear to be doing
3. Any important context from recent history
4. Anything they should be aware of

Keep your response to 2-3 short paragraphs maximum. Be warm and supportive.
""")

        # GPS data
        if data.get('gps_data'):
            latest_gps = data['gps_data'][-1] if data['gps_data'] else None
            if latest_gps:
                prompt_parts.append(f"\n--- CURRENT LOCATION ---")
                prompt_parts.append(f"Latitude: {latest_gps.get('latitude')}")
                prompt_parts.append(f"Longitude: {latest_gps.get('longitude')}")
                prompt_parts.append(f"Time: {latest_gps.get('timestamp')}")

                # Include recent movement pattern if available
                if len(data['gps_data']) > 1:
                    prompt_parts.append(f"\nRecent locations (last {len(data['gps_data'])} updates):")
                    for gps in data['gps_data'][-5:]:  # Last 5 positions
                        prompt_parts.append(
                            f"  - {gps.get('latitude'):.6f}, {gps.get('longitude'):.6f} at {gps.get('timestamp')}"
                        )

        # Photo data
        if data.get('photos'):
            prompt_parts.append(f"\n--- PHOTOS CAPTURED ---")
            prompt_parts.append(f"Number of photos taken: {len(data['photos'])}")
            prompt_parts.append("Most recent photos:")
            for photo in data['photos'][-3:]:  # Last 3 photos
                prompt_parts.append(f"  - {photo.get('filename')} at {photo.get('timestamp')}")
            prompt_parts.append(
                "\nNote: Photo analysis will be added in future updates. For now, "
                "provide general context based on location and time."
            )

        # Audio data
        if data.get('audio_chunks'):
            prompt_parts.append(f"\n--- AUDIO DATA ---")
            prompt_parts.append(f"Audio chunks captured: {data['audio_chunks']}")
            prompt_parts.append(
                "Note: Audio transcription will be added in future updates."
            )

        # Previous context
        if self.context_history:
            prompt_parts.append(f"\n--- RECENT HISTORY ---")
            prompt_parts.append(f"Previous state (for context): {self.context_history[-1]['response']}")

        # Final instruction
        prompt_parts.append(
            "\n--- YOUR TASK ---\n"
            "Based on all the above information, provide a clear, supportive summary of "
            "where the person is and what's happening. If you can identify the location from "
            "coordinates, mention specific place names. Be specific and reassuring."
        )

        return "\n".join(prompt_parts)

    def analyze_photo(self, photo_path: str) -> str:
        """
        Analyze a photo using Gemini Vision capabilities

        Args:
            photo_path: Path to the photo file

        Returns:
            Description of what's in the photo
        """
        try:
            # Upload image to Gemini
            image_file = genai.upload_file(photo_path)

            # Create vision prompt
            vision_prompt = """Describe what you see in this image in 2-3 sentences.
Focus on: location type (indoor/outdoor), people, objects, activities,
and anything important for someone who might not remember taking this photo."""

            # Generate response
            response = self.model.generate_content([vision_prompt, image_file])

            return response.text

        except Exception as e:
            print(f"[Gemini Vision Error] {str(e)}")
            return f"Unable to analyze photo: {str(e)}"

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio file

        Args:
            audio_path: Path to the audio file

        Returns:
            Transcription of the audio
        """
        try:
            # Upload audio to Gemini
            audio_file = genai.upload_file(audio_path)

            # Create transcription prompt
            transcription_prompt = """Transcribe this audio clearly.
If there are multiple speakers, indicate who is speaking when possible.
If the audio is unclear or silent, just say so."""

            # Generate response
            response = self.model.generate_content([transcription_prompt, audio_file])

            return response.text

        except Exception as e:
            print(f"[Gemini Audio Error] {str(e)}")
            return f"Unable to transcribe audio: {str(e)}"
