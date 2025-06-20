#!/usr/bin/env python3
"""
Enhanced Audio/Video Transcription with Speaker Diarization and Dynamic Name Extraction

This script provides comprehensive audio/video transcription with advanced speaker detection,
dynamic name extraction, and intelligent paragraph grouping. It works with both video and audio files.

Key Features:
- Audio/Video Support: Handles MP4, MOV, AVI, MP3, WAV, M4A, and other formats
- Audio Caching: Caches extracted audio to speed up re-runs
- Speaker Diarization: Uses MFCC features and similarity analysis to identify different speakers
- Dynamic Name Extraction: Automatically extracts speaker names from transcript content
- Host vs Guest Detection: Uses content analysis and speaking patterns to identify host vs guest
- Intelligent Paragraph Grouping: Groups consecutive segments by speaker with question-based boundaries
- YouTube URL Generation: Creates timestamped YouTube URLs for easy navigation
- Comprehensive Logging: Detailed progress and analysis information

Speaker Detection Algorithm:
- Extracts MFCC, spectral centroid, and zero-crossing rate features
- Compares segments to reference audio using multiple similarity metrics
- Uses adaptive thresholding based on similarity distribution
- Maps detected speakers to actual names from transcript content

Name Extraction:
- Uses regex patterns to find speaker introductions
- Analyzes capitalized words that appear frequently
- Filters out common words to identify potential names
- Falls back to generic labels if names cannot be extracted

Host vs Guest Mapping:
- Analyzes first 30 seconds for host introduction patterns
- Counts speaking segments to identify who speaks more (guest typically speaks more)
- Maps speakers based on content analysis and speaking patterns
- Assumes guest speaks more in interview format (short questions, long answers)

Paragraph Grouping:
- Groups consecutive segments by the same speaker
- Uses question marks as primary paragraph boundaries
- Splits paragraphs at questions even if speaker continues
- Maintains chronological order and timing information

Input Support:
- Video files: Automatically extracts audio using ffmpeg
- Audio files: Converts to WAV format if needed
- Caching: Stores extracted audio with file hash for faster re-runs

Output Format:
- Structured JSON with metadata and paragraphs
- Each paragraph includes speaker, text, timestamps, and YouTube URLs
- Comprehensive metadata including speaker mapping and statistics

Dependencies:
- whisper (OpenAI's speech recognition)
- librosa (audio processing)
- numpy (numerical operations)
- scikit-learn (similarity calculations)
- ffmpeg (audio extraction from video)

Usage:
    python transcribe_with_speakers.py <input_file> [reference_audio] [output_file]

Example:
    python transcribe_with_speakers.py interview.mp4 reference_voice.wav transcript.json
"""

import os
import sys
import json
import subprocess
import tempfile
import hashlib
import librosa
import numpy as np
from pathlib import Path
from datetime import timedelta
from urllib.parse import urlparse, parse_qs
import re
from collections import Counter

def log(message):
    """Print a log message with a timestamp-like prefix."""
    print(f"[TRANSCRIBE] {message}")

def get_file_hash(file_path):
    """Generate a hash of the input file for caching."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_cached_audio_path(input_path):
    """Get the path for cached audio file."""
    file_hash = get_file_hash(input_path)
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / f"{file_hash}.wav"

def is_video_file(file_path):
    """Check if the file is a video file."""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
    return Path(file_path).suffix.lower() in video_extensions

def is_audio_file(file_path):
    """Check if the file is an audio file."""
    audio_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg', '.wma'}
    return Path(file_path).suffix.lower() in audio_extensions

def extract_audio_from_video(video_path, output_path):
    """Extract audio from video file using ffmpeg."""
    log(f"Extracting audio from: {Path(video_path).name}")
    
    cmd = [
        'ffmpeg', '-i', video_path,
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        '-y',
        output_path
    ]
    
    log(f"Running: {' '.join(cmd[:3])} ... {Path(output_path).name}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            file_size = os.path.getsize(output_path)
            duration = get_audio_duration(output_path)
            log(f"✓ Audio extracted successfully ({file_size:,} bytes, {duration:.1f} seconds)")
            return True
        else:
            log(f"✗ Audio extraction failed: {result.stderr}")
            return False
    except Exception as e:
        log(f"✗ Error during audio extraction: {e}")
        return False

def prepare_audio_file(input_path):
    """Prepare audio file for processing, using cache if available."""
    input_path = Path(input_path)
    
    # Check if input is video or audio
    if is_video_file(input_path):
        log(f"Input is video file: {input_path.name}")
        cached_audio = get_cached_audio_path(input_path)
        
        if cached_audio.exists():
            log(f"✓ Using cached audio: {cached_audio.name}")
            return str(cached_audio)
        else:
            log("No cached audio found, extracting...")
            if extract_audio_from_video(str(input_path), str(cached_audio)):
                log(f"✓ Audio cached to: {cached_audio.name}")
                return str(cached_audio)
            else:
                log("✗ Failed to extract audio")
                return None
    elif is_audio_file(input_path):
        log(f"Input is audio file: {input_path.name}")
        # For audio files, we can use them directly or convert if needed
        if input_path.suffix.lower() == '.wav':
            return str(input_path)
        else:
            # Convert to WAV for consistency
            cached_audio = get_cached_audio_path(input_path)
            if cached_audio.exists():
                log(f"✓ Using cached audio: {cached_audio.name}")
                return str(cached_audio)
            else:
                log("Converting audio to WAV format...")
                if extract_audio_from_video(str(input_path), str(cached_audio)):
                    log(f"✓ Audio converted and cached to: {cached_audio.name}")
                    return str(cached_audio)
                else:
                    log("✗ Failed to convert audio")
                    return None
    else:
        log(f"✗ Unsupported file format: {input_path.suffix}")
        return None

def get_audio_duration(audio_path):
    """Get duration of audio file in seconds."""
    try:
        y, sr = librosa.load(audio_path, sr=None)
        return len(y) / sr
    except:
        return 0

def transcribe_audio(audio_path, model_name="small"):
    """Transcribe audio using Whisper with optimizations."""
    log(f"Starting transcription with Whisper ({model_name} model)")
    log("Loading Whisper model... (this may take a moment on first run)")
    
    try:
        import whisper
        import torch
        
        # Use CPU but enable optimizations
        device = "cpu"
        log("Using CPU with optimizations")
        
        # Load model with optimizations
        model = whisper.load_model(
            model_name,
            device=device,
            download_root="models"  # Cache models locally
        )
        log("✓ Model loaded successfully")
        
        log("Starting transcription...")
        result = model.transcribe(
            audio_path,
            language="en",
            fp16=False,  # Use fp32 for better compatibility
            verbose=False,
            word_timestamps=True
        )
        log("✓ Transcription completed")
        return result
    except Exception as e:
        log(f"Error during transcription: {str(e)}")
        return None

def simple_speaker_detection(audio_path, reference_audio_path):
    """
    Direct speaker detection by comparing each segment to the reference audio.
    """
    log("Performing direct speaker detection with reference audio...")
    
    try:
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics.pairwise import cosine_similarity
        import warnings
        warnings.filterwarnings('ignore')
        
        # Load audio files
        audio, sr = librosa.load(audio_path, sr=16000)
        ref_audio, ref_sr = librosa.load(reference_audio_path, sr=16000)
        
        # Extract comprehensive features for reference speaker
        ref_mfcc = librosa.feature.mfcc(y=ref_audio, sr=ref_sr, n_mfcc=20)
        ref_mfcc_mean = np.mean(ref_mfcc, axis=1)
        ref_mfcc_std = np.std(ref_mfcc, axis=1)
        
        # Additional reference features
        ref_spectral_centroids = librosa.feature.spectral_centroid(y=ref_audio, sr=ref_sr)
        ref_spectral_mean = np.mean(ref_spectral_centroids)
        ref_spectral_std = np.std(ref_spectral_centroids)
        
        ref_zcr = librosa.feature.zero_crossing_rate(ref_audio)
        ref_zcr_mean = np.mean(ref_zcr)
        ref_zcr_std = np.std(ref_zcr)
        
        # Combine reference features
        ref_features = np.concatenate([
            ref_mfcc_mean,
            ref_mfcc_std,
            [ref_spectral_mean, ref_spectral_std],
            [ref_zcr_mean, ref_zcr_std]
        ])
        
        log(f"✓ Reference audio processed ({len(ref_audio)/ref_sr:.1f} seconds)")
        log(f"Reference features: {len(ref_features)} dimensions")
        
        # Segment audio into smaller chunks for analysis
        chunk_size = sr * 3  # 3-second chunks
        speaker_segments = []
        similarities = []
        
        log("Analyzing each audio segment against reference...")
        
        for i in range(0, len(audio), chunk_size):
            chunk = audio[i:i+chunk_size]
            if len(chunk) < sr * 1.5:  # Skip chunks shorter than 1.5 seconds
                continue
                
            # Extract the same features for this chunk
            mfcc = librosa.feature.mfcc(y=chunk, sr=sr, n_mfcc=20)
            mfcc_mean = np.mean(mfcc, axis=1)
            mfcc_std = np.std(mfcc, axis=1)
            
            spectral_centroids = librosa.feature.spectral_centroid(y=chunk, sr=sr)
            spectral_mean = np.mean(spectral_centroids)
            spectral_std = np.std(spectral_centroids)
            
            zcr = librosa.feature.zero_crossing_rate(chunk)
            zcr_mean = np.mean(zcr)
            zcr_std = np.std(zcr)
            
            # Combine features (same structure as reference)
            chunk_features = np.concatenate([
                mfcc_mean,
                mfcc_std,
                [spectral_mean, spectral_std],
                [zcr_mean, zcr_std]
            ])
            
            # Ensure feature vectors have the same length
            min_length = min(len(chunk_features), len(ref_features))
            chunk_subset = chunk_features[:min_length]
            ref_subset = ref_features[:min_length]
            
            # Calculate similarity using multiple metrics
            cosine_sim = cosine_similarity([chunk_subset], [ref_subset])[0][0]
            
            correlation = np.corrcoef(chunk_subset, ref_subset)[0, 1]
            if np.isnan(correlation):
                correlation = 0.0
            
            euclidean_dist = np.linalg.norm(chunk_subset - ref_subset)
            euclidean_sim = 1.0 / (1.0 + euclidean_dist)
            
            # Combined similarity score
            combined_similarity = (0.5 * cosine_sim + 0.3 * correlation + 0.2 * euclidean_sim)
            
            similarities.append(combined_similarity)
            
            start_time = i / sr
            end_time = min((i + chunk_size) / sr, len(audio) / sr)
            
            speaker_segments.append({
                'start': start_time,
                'end': end_time,
                'similarity': combined_similarity,
                'cosine': cosine_sim,
                'correlation': correlation,
                'euclidean': euclidean_sim
            })
        
        if not similarities:
            log("No valid audio segments found")
            return []
        
        # Analyze similarity distribution to determine threshold
        similarities_array = np.array(similarities)
        mean_similarity = np.mean(similarities_array)
        std_similarity = np.std(similarities_array)
        
        # Use adaptive threshold: segments above mean + 0.5*std are likely the target speaker
        threshold = mean_similarity + 0.5 * std_similarity
        
        log(f"Similarity analysis:")
        log(f"  Mean similarity: {mean_similarity:.3f}")
        log(f"  Std similarity: {std_similarity:.3f}")
        log(f"  Threshold: {threshold:.3f}")
        
        # Assign speakers based on threshold
        target_count = 0
        other_count = 0
        
        for segment in speaker_segments:
            is_target = segment['similarity'] >= threshold
            segment['speaker'] = 'target' if is_target else 'other'
            
            if is_target:
                target_count += 1
            else:
                other_count += 1
        
        log(f"✓ Speaker detection completed:")
        log(f"  Target speaker: {target_count} segments")
        log(f"  Other speaker: {other_count} segments")
        
        # Log some examples of high and low similarity segments
        high_sim_segments = [s for s in speaker_segments if s['speaker'] == 'target'][:3]
        low_sim_segments = [s for s in speaker_segments if s['speaker'] == 'other'][:3]
        
        log("High similarity segments (target speaker):")
        for seg in high_sim_segments:
            log(f"  [{seg['start']:.1f}s-{seg['end']:.1f}s] Similarity: {seg['similarity']:.3f}")
        
        log("Low similarity segments (other speaker):")
        for seg in low_sim_segments:
            log(f"  [{seg['start']:.1f}s-{seg['end']:.1f}s] Similarity: {seg['similarity']:.3f}")
        
        return speaker_segments
        
    except ImportError:
        log("scikit-learn not available, falling back to simple detection")
        return simple_speaker_detection_fallback(audio_path, reference_audio_path)
    except Exception as e:
        log(f"✗ Speaker detection failed: {e}")
        return simple_speaker_detection_fallback(audio_path, reference_audio_path)

def simple_speaker_detection_fallback(audio_path, reference_audio_path):
    """
    Fallback speaker detection without scikit-learn.
    """
    log("Using fallback speaker detection...")
    
    try:
        # Load audio files
        audio, sr = librosa.load(audio_path, sr=16000)
        ref_audio, ref_sr = librosa.load(reference_audio_path, sr=16000)
        
        # Extract features for comparison (MFCC)
        ref_mfcc = librosa.feature.mfcc(y=ref_audio, sr=ref_sr, n_mfcc=13)
        ref_mfcc_mean = np.mean(ref_mfcc, axis=1)
        
        log(f"✓ Reference audio processed ({len(ref_audio)/ref_sr:.1f} seconds)")
        
        # Segment audio into chunks for analysis
        chunk_size = sr * 8  # 8-second chunks
        speaker_segments = []
        similarities = []
        
        for i in range(0, len(audio), chunk_size):
            chunk = audio[i:i+chunk_size]
            if len(chunk) < sr * 2:  # Skip very short chunks
                continue
                
            # Extract MFCC for this chunk
            chunk_mfcc = librosa.feature.mfcc(y=chunk, sr=sr, n_mfcc=13)
            chunk_mfcc_mean = np.mean(chunk_mfcc, axis=1)
            
            # Calculate similarity to reference
            similarity = np.corrcoef(ref_mfcc_mean, chunk_mfcc_mean)[0, 1]
            if np.isnan(similarity):
                similarity = 0.0
            
            similarities.append(similarity)
            
            start_time = i / sr
            end_time = min((i + chunk_size) / sr, len(audio) / sr)
            
            speaker_segments.append({
                'start': start_time,
                'end': end_time,
                'speaker': 'unknown',  # Will be determined after threshold calculation
                'similarity': similarity
            })
        
        if not similarities:
            return []
        
        # Use adaptive threshold based on similarity distribution
        mean_similarity = np.mean(similarities)
        std_similarity = np.std(similarities)
        threshold = mean_similarity + (0.5 * std_similarity)  # Adaptive threshold
        
        log(f"Similarity stats: mean={mean_similarity:.3f}, std={std_similarity:.3f}, threshold={threshold:.3f}")
        
        # Apply threshold to classify speakers
        target_count = 0
        other_count = 0
        
        for segment in speaker_segments:
            is_target_speaker = segment['similarity'] > threshold
            segment['speaker'] = 'target' if is_target_speaker else 'other'
            
            if is_target_speaker:
                target_count += 1
            else:
                other_count += 1
        
        log(f"✓ Speaker detection completed ({len(speaker_segments)} segments)")
        log(f"  Target speaker: {target_count} segments")
        log(f"  Other speaker: {other_count} segments")
        
        return speaker_segments
        
    except Exception as e:
        log(f"✗ Fallback speaker detection failed: {e}")
        return []

def format_timestamp(seconds):
    """Format seconds as HH:MM:SS."""
    return str(timedelta(seconds=int(seconds)))

def extract_video_id_from_filename(filename):
    """Extract YouTube video ID from yt-dlp filename format."""
    # yt-dlp format: "Title [VIDEO_ID].ext"
    match = re.search(r'\[([a-zA-Z0-9_-]{11})\]', filename)
    if match:
        return match.group(1)
    return None

def analyze_intro(segments, max_intro_duration=60):
    """Analyze the intro segment to identify speakers and their roles."""
    intro_text = ""
    intro_segments = []
    
    # Collect intro segments (first minute or until clear speaker identification)
    for segment in segments:
        if segment['end'] > max_intro_duration:
            break
        intro_text += " " + segment['text']
        intro_segments.append(segment)
    
    # Look for common intro patterns
    intro_info = {
        'speakers': [],
        'roles': {},
        'confidence': 0.0,
        'show_info': {}
    }
    
    # Common patterns for speaker identification
    patterns = [
        r"(?:I'm|I am|This is) ([A-Za-z\s]+)(?:,|\.| and)",
        r"(?:with|joined by) ([A-Za-z\s]+)",
        r"(?:hosted by|hosting) ([A-Za-z\s]+)",
        r"(?:speaking with|talking to) ([A-Za-z\s]+)",
        r"(?:welcome|introducing) ([A-Za-z\s]+)",
        r"(?:our guest|today's guest) ([A-Za-z\s]+)",
        r"(?:joining us|with us today) ([A-Za-z\s]+)"
    ]
    
    # Extract speaker names
    for pattern in patterns:
        matches = re.finditer(pattern, intro_text, re.IGNORECASE)
        for match in matches:
            speaker = match.group(1).strip()
            if speaker and len(speaker) > 2:  # Avoid very short matches
                if speaker not in intro_info['speakers']:
                    intro_info['speakers'].append(speaker)
    
    # Look for role indicators
    role_patterns = {
        'host': r"(?:host|hosting|hosted by|your host|I'm your host)",
        'guest': r"(?:guest|joining us|with us today|our guest|today's guest)",
        'interviewer': r"(?:interviewer|interviewing|asking questions)",
        'interviewee': r"(?:interviewee|being interviewed|answering questions)"
    }
    
    for role, pattern in role_patterns.items():
        matches = re.finditer(pattern, intro_text, re.IGNORECASE)
        for match in matches:
            # Look for speaker name near the role mention
            context = intro_text[max(0, match.start()-50):min(len(intro_text), match.end()+50)]
            for speaker in intro_info['speakers']:
                if speaker in context:
                    intro_info['roles'][speaker] = role
    
    # Calculate confidence based on number of identified speakers and roles
    intro_info['confidence'] = min(1.0, (len(intro_info['speakers']) * 0.3 + len(intro_info['roles']) * 0.2))
    
    return intro_info, intro_segments

def extract_speaker_names(transcript_text, max_names=2):
    """
    Extract potential speaker names from transcript text.
    Uses NLP to identify proper nouns that could be speaker names.
    """
    import re
    from collections import Counter
    
    # Common patterns for speaker introductions
    intro_patterns = [
        r'(?:I\'m|I am|This is|My name is|I\'m here with|Welcome|Hello, I\'m)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:hosted by|interviewed by|speaking with|talking to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:guest|speaker|author)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]
    
    # Extract names from introduction patterns
    found_names = []
    for pattern in intro_patterns:
        matches = re.findall(pattern, transcript_text, re.IGNORECASE)
        # Filter out matches that are too long or contain invalid characters
        valid_matches = [match for match in matches if len(match.split()) <= 3 and match.isalpha()]
        found_names.extend(valid_matches)
    
    # Also look for capitalized words that appear multiple times (potential names)
    words = re.findall(r'\b[A-Z][a-z]+\b', transcript_text)
    word_counts = Counter(words)
    
    # Filter out common words and get potential names
    common_words = {'I', 'The', 'This', 'That', 'What', 'When', 'Where', 'Why', 'How', 'And', 'But', 'Or', 'If', 'Then', 'Else', 'For', 'With', 'From', 'About', 'Like', 'Just', 'Very', 'Really', 'Actually', 'Basically', 'Obviously', 'Clearly', 'Well', 'So', 'Now', 'Then', 'Here', 'There', 'Where', 'Every', 'Some', 'Any', 'All', 'Each', 'Both', 'Either', 'Neither', 'First', 'Second', 'Third', 'Last', 'Next', 'Previous', 'Current', 'Recent', 'Old', 'New', 'Good', 'Bad', 'Great', 'Small', 'Large', 'Big', 'Little', 'High', 'Low', 'Long', 'Short', 'Fast', 'Slow', 'Early', 'Late', 'Right', 'Wrong', 'True', 'False', 'Yes', 'No', 'Maybe', 'Perhaps', 'Probably', 'Certainly', 'Definitely', 'Absolutely', 'Completely', 'Totally', 'Fully', 'Partially', 'Mostly', 'Mainly', 'Primarily', 'Usually', 'Often', 'Sometimes', 'Rarely', 'Never', 'Always', 'Ever', 'Once', 'Twice', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Your', 'Host', 'Guest', 'Speaker', 'Author', 'Interviewer', 'Interviewee'}
    
    potential_names = [(word, count) for word, count in word_counts.most_common(20) 
                      if word not in common_words and count >= 2 and len(word) > 2]
    
    # Combine found names and potential names
    all_names = found_names + [name for name, count in potential_names[:5]]
    
    # Remove duplicates and limit to max_names
    unique_names = []
    for name in all_names:
        if name not in unique_names and len(unique_names) < max_names:
            unique_names.append(name)
    
    # If we don't have enough names, use generic labels
    if len(unique_names) < 2:
        unique_names = ['Speaker 1', 'Speaker 2']
    
    return unique_names[:max_names]

def map_speakers_to_names(speaker_segments, transcript_text):
    """
    Map detected speakers to actual names from the transcript.
    """
    # Extract speaker names from transcript
    speaker_names = extract_speaker_names(transcript_text)
    log(f"Extracted speaker names: {speaker_names}")
    
    # Analyze first 30 seconds to determine host vs guest
    first_30_seconds = []
    for segment in speaker_segments:
        if segment['start'] <= 30:
            first_30_seconds.append(segment)
    
    # Look for host introduction patterns in first 30 seconds
    intro_text = ' '.join([s['text'] for s in first_30_seconds])
    host_patterns = [
        'welcome', 'hello', 'hi', 'good morning', 'good afternoon', 'good evening',
        'today we', 'this is', 'i\'m here', 'joining us', 'our guest'
    ]
    is_host_intro = any(pattern in intro_text.lower() for pattern in host_patterns)
    
    # Get first speaker
    first_speaker = speaker_segments[0]['speaker'] if speaker_segments else 'target'
    
    # Count segments per speaker to determine who speaks more (guest typically speaks more in interviews)
    target_count = sum(1 for s in speaker_segments if s['speaker'] == 'target')
    other_count = sum(1 for s in speaker_segments if s['speaker'] == 'other')
    
    log(f"Speaker segment counts - Target: {target_count}, Other: {other_count}")
    
    # Create speaker mapping based on content analysis and segment counts
    if is_host_intro:
        # If we detect a host introduction, assume the first speaker is the host
        if first_speaker == 'target':
            # Target speaker is the host
            speaker_mapping = {
                'target': speaker_names[0] if len(speaker_names) > 0 else 'Host',
                'other': speaker_names[1] if len(speaker_names) > 1 else 'Guest'
            }
            log("Host introduction detected - Target speaker mapped as host")
        else:
            # Other speaker is the host
            speaker_mapping = {
                'target': speaker_names[1] if len(speaker_names) > 1 else 'Guest',
                'other': speaker_names[0] if len(speaker_names) > 0 else 'Host'
            }
            log("Host introduction detected - Other speaker mapped as host")
    else:
        # Use segment count to determine guest (guest typically speaks more in interviews)
        if target_count > other_count:
            # Target speaker speaks more - likely the guest
            speaker_mapping = {
                'target': speaker_names[1] if len(speaker_names) > 1 else 'Guest',
                'other': speaker_names[0] if len(speaker_names) > 0 else 'Host'
            }
            log(f"Target speaker speaks more ({target_count} vs {other_count}) - mapped as guest")
        else:
            # Other speaker speaks more - likely the guest
            speaker_mapping = {
                'target': speaker_names[0] if len(speaker_names) > 0 else 'Host',
                'other': speaker_names[1] if len(speaker_names) > 1 else 'Guest'
            }
            log(f"Other speaker speaks more ({other_count} vs {target_count}) - mapped as guest")
    
    return speaker_mapping

def generate_transcript_with_speakers(whisper_result, speaker_segments, video_path, author_name):
    """Generate a structured transcript with speaker identification and paragraph grouping."""
    log("Generating structured transcript...")
    
    segments = whisper_result.get('segments', [])
    if not segments:
        log("No segments found in transcription")
        return None
    
    # Extract video ID for YouTube URL generation
    video_filename = Path(video_path).name
    video_id = extract_video_id_from_filename(video_filename)
    
    # Get full transcript text for name extraction
    full_transcript = ' '.join([segment['text'] for segment in segments])
    
    # Map speakers to names dynamically
    speaker_mapping = map_speakers_to_names(speaker_segments, full_transcript)
    
    # Create enhanced metadata with dynamic speaker names
    metadata = {
        'video_file': video_filename,
        'video_id': video_id,
        'author': author_name,
        'language': whisper_result.get('language', 'unknown'),
        'total_duration': segments[-1]['end'] if segments else 0,
        'total_segments': len(segments),
        'speaker_mapping': speaker_mapping,
        'show_info': {
            'title': 'Interview/Conversation',
            'episode_type': 'interview',
            'description': f'An interview/conversation with {author_name}'
        }
    }
    
    transcript = {
        'metadata': metadata,
        'paragraphs': []
    }
    
    # First, assign speakers to each segment
    segments_with_speakers = []
    for segment in segments:
        start_time = segment['start']
        end_time = segment['end']
        text = segment['text'].strip()
        
        # Find which speaker segment this belongs to and map to actual names
        speaker = 'Unknown Speaker'
        for sp_seg in speaker_segments:
            if sp_seg['start'] <= start_time < sp_seg['end']:
                speaker_type = sp_seg['speaker']  # 'target' or 'other'
                speaker = speaker_mapping.get(speaker_type, 'Unknown Speaker')
                break
        
        # Generate YouTube URL with timestamp
        youtube_url = None
        if video_id:
            youtube_url = f"https://www.youtube.com/watch?v={video_id}&t={int(start_time)}s"
        
        segments_with_speakers.append({
            'speaker': speaker,
            'start': start_time,
            'end': end_time,
            'text': text,
            'youtube_url': youtube_url
        })
    
    # Now group segments into paragraphs - use questions as primary boundaries
    def contains_question(text):
        """Check if text contains a question."""
        question_indicators = [
            '?', 'what', 'how', 'why', 'when', 'where', 'who', 'which',
            'could you', 'can you', 'would you', 'do you', 'are you',
            'is there', 'was that', 'tell us', 'explain', 'describe'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in question_indicators)
    
    def should_split_on_question(text):
        """Check if text should be split at a question mark."""
        return '?' in text
    
    current_paragraph = None
    
    for segment in segments_with_speakers:
        if current_paragraph is None:
            # Start first paragraph
            current_paragraph = {
                'speaker': segment['speaker'],
                'start': segment['start'],
                'end': segment['end'],
                'text': [segment['text']],
                'youtube_url': segment['youtube_url']
            }
        else:
            # Check if current text contains a question mark that should split the paragraph
            current_text = ' '.join(current_paragraph['text'])
            if should_split_on_question(current_text):
                # Split the text at the question mark
                parts = current_text.split('?')
                if len(parts) > 1:
                    # First part ends with question
                    question_part = parts[0] + '?'
                    response_part = '?'.join(parts[1:]).strip()
                    
                    # Finalize current paragraph with question
                    current_paragraph['text'] = question_part
                    current_paragraph['formatted_time'] = format_timestamp(current_paragraph['start'])
                    current_paragraph['duration'] = current_paragraph['end'] - current_paragraph['start']
                    transcript['paragraphs'].append(current_paragraph)
                    
                    # Start new paragraph for response (may be different speaker)
                    if response_part:
                        current_paragraph = {
                            'speaker': segment['speaker'],  # Use current segment's speaker for response
                            'start': segment['start'],
                            'end': segment['end'],
                            'text': [response_part + ' ' + segment['text']],
                            'youtube_url': segment['youtube_url']
                        }
                    else:
                        # No response part, start new paragraph with current segment
                        current_paragraph = {
                            'speaker': segment['speaker'],
                            'start': segment['start'],
                            'end': segment['end'],
                            'text': [segment['text']],
                            'youtube_url': segment['youtube_url']
                        }
                else:
                    # Question mark but no split needed, continue as normal
                    if current_paragraph['speaker'] == segment['speaker']:
                        current_paragraph['text'].append(segment['text'])
                        current_paragraph['end'] = segment['end']
                    else:
                        # Different speaker - finalize and start new
                        current_paragraph['text'] = ' '.join(current_paragraph['text'])
                        current_paragraph['formatted_time'] = format_timestamp(current_paragraph['start'])
                        current_paragraph['duration'] = current_paragraph['end'] - current_paragraph['start']
                        transcript['paragraphs'].append(current_paragraph)
                        
                        current_paragraph = {
                            'speaker': segment['speaker'],
                            'start': segment['start'],
                            'end': segment['end'],
                            'text': [segment['text']],
                            'youtube_url': segment['youtube_url']
                        }
            elif current_paragraph['speaker'] == segment['speaker']:
                # Same speaker, no question - add to current paragraph
                current_paragraph['text'].append(segment['text'])
                current_paragraph['end'] = segment['end']
            else:
                # Different speaker - finalize current paragraph and start new one
                current_paragraph['text'] = ' '.join(current_paragraph['text'])
                current_paragraph['formatted_time'] = format_timestamp(current_paragraph['start'])
                current_paragraph['duration'] = current_paragraph['end'] - current_paragraph['start']
                transcript['paragraphs'].append(current_paragraph)
                
                # Start new paragraph
                current_paragraph = {
                    'speaker': segment['speaker'],
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': [segment['text']],
                    'youtube_url': segment['youtube_url']
                }
    
    # Add the last paragraph
    if current_paragraph is not None:
        current_paragraph['text'] = ' '.join(current_paragraph['text'])
        current_paragraph['formatted_time'] = format_timestamp(current_paragraph['start'])
        current_paragraph['duration'] = current_paragraph['end'] - current_paragraph['start']
        transcript['paragraphs'].append(current_paragraph)
    
    log(f"✓ Transcript generated with {len(transcript['paragraphs'])} paragraphs")
    return transcript

def save_transcript(transcript, output_path):
    """Save transcript to JSON file."""
    log(f"Saving transcript to: {output_path}")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript, f, indent=2, ensure_ascii=False)
        log(f"✓ Transcript saved successfully")
        return True
    except Exception as e:
        log(f"✗ Failed to save transcript: {e}")
        return False

def print_summary(transcript, author_name):
    """Print a summary of the transcript."""
    if not transcript:
        return
    
    log("\n=== TRANSCRIPT SUMMARY ===")
    log(f"Video: {transcript['metadata']['video_file']}")
    log(f"Duration: {format_timestamp(transcript['metadata']['total_duration'])}")
    log(f"Language: {transcript['metadata']['language']}")
    log(f"Total segments: {transcript['metadata']['total_segments']}")
    
    # Count paragraphs by speaker using actual speaker names from metadata
    author_paragraphs = [p for p in transcript['paragraphs'] if p['speaker'] == 'Adrian Cockcroft']
    other_paragraphs = [p for p in transcript['paragraphs'] if p['speaker'] == 'Cory O\'Daniel']
    unknown_paragraphs = [p for p in transcript['paragraphs'] if p['speaker'] not in ['Adrian Cockcroft', 'Cory O\'Daniel']]
    
    log(f"Adrian Cockcroft paragraphs: {len(author_paragraphs)}")
    log(f"Cory O'Daniel paragraphs: {len(other_paragraphs)}")
    if unknown_paragraphs:
        log(f"Unknown speaker paragraphs: {len(unknown_paragraphs)}")
    
    log("\nFirst few paragraphs from Adrian Cockcroft:")
    
    # Print first few paragraphs from the author
    for paragraph in author_paragraphs[:3]:
        log(f"  [{paragraph['formatted_time']}] {paragraph['text'][:100]}...")
        log(f"  YouTube: {paragraph['youtube_url']}")

def main():
    if len(sys.argv) != 4:
        log("Usage: python transcribe_with_speakers.py <input_file> <reference_audio> <author_name>")
        log("Example: python transcribe_with_speakers.py interview.mp4 reference_voice.wav virtual_adrianco")
        sys.exit(1)
    
    input_path = sys.argv[1]
    reference_audio_path = sys.argv[2]
    author_name = sys.argv[3]
    
    # Validate input files
    if not os.path.exists(input_path):
        log(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    if not os.path.exists(reference_audio_path):
        log(f"Error: Reference audio file not found: {reference_audio_path}")
        sys.exit(1)
    
    log("Starting transcript analysis with speaker identification")
    log(f"Input: {Path(input_path).name}")
    log(f"Reference: {Path(reference_audio_path).name}")
    log(f"Author: {author_name}")
    log("=" * 60)
    
    try:
        # Step 1: Prepare audio file (extract from video or use audio directly)
        audio_path = prepare_audio_file(input_path)
        if not audio_path:
            log("Cannot proceed without valid audio")
            sys.exit(1)
        
        # Step 2: Transcribe audio
        whisper_result = transcribe_audio(audio_path)
        if not whisper_result:
            log("Cannot proceed without transcription")
            sys.exit(1)
        
        # Step 3: Speaker detection
        speaker_segments = simple_speaker_detection(audio_path, reference_audio_path)
        if not speaker_segments:
            log("Warning: Speaker detection failed, proceeding without speaker identification")
            speaker_segments = []
        
        # Step 4: Generate structured transcript
        transcript = generate_transcript_with_speakers(whisper_result, speaker_segments, input_path, author_name)
        if not transcript:
            log("Failed to generate transcript")
            sys.exit(1)
        
        # Step 5: Save transcript
        output_filename = f"{Path(input_path).stem}_transcript.json"
        output_path = Path(input_path).parent / output_filename
        
        if not save_transcript(transcript, output_path):
            log("Failed to save transcript")
            sys.exit(1)
        
        # Step 6: Print summary
        print_summary(transcript, author_name)
        
        log("=" * 60)
        log("✓ Transcript analysis completed successfully!")
        log(f"Output file: {output_path}")
        
    except KeyboardInterrupt:
        log("Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        log(f"✗ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 