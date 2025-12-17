#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to demonstrate the enhanced logging system for video processing.

This script simulates video processing operations to show how the logging
system tracks dimensions, aspect ratios, and processing steps.
"""

import os
import sys
import time
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from snippet_remixer.logging_config import setup_logging, get_logger, LoggingContext, log_video_info, log_ffmpeg_command


def test_basic_logging():
    """Test basic logging functionality."""
    print("\n=== Testing Basic Logging ===")
    
    # Set up logging
    logger, video_filter = setup_logging(
        log_dir="test_logs",
        log_level=logging.DEBUG,
        console_level=logging.INFO
    )
    
    # Basic log messages
    logger.info("Testing basic info message")
    logger.debug("Testing debug message (should appear in file only)")
    logger.warning("Testing warning message")
    logger.error("Testing error message")
    
    return logger, video_filter


def test_video_context_logging(logger, video_filter):
    """Test logging with video context."""
    print("\n=== Testing Video Context Logging ===")
    
    # Test with video context
    with LoggingContext(video_filter, video_file="test_video.mp4"):
        logger.info("Processing video file")
        
        # Add dimensions
        with LoggingContext(video_filter, dimensions="1920x1080", aspect_ratio="1.778"):
            logger.info("Video dimensions extracted")
            logger.debug("Detailed dimension info logged")
    
    # Context should be cleared
    logger.info("Context cleared - no video info should appear")


def test_ffmpeg_command_logging(logger):
    """Test FFmpeg command logging."""
    print("\n=== Testing FFmpeg Command Logging ===")
    
    # Simple command
    simple_cmd = ["ffmpeg", "-i", "input.mp4", "-c:v", "libx264", "output.mp4"]
    log_ffmpeg_command(logger, simple_cmd)
    
    # Complex command with filters
    complex_cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-i", "input.mp4",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-y", "output.mp4"
    ]
    log_ffmpeg_command(logger, complex_cmd, level=logging.INFO)


def test_video_info_logging(logger):
    """Test video information logging."""
    print("\n=== Testing Video Info Logging ===")
    
    # Log various video configurations
    test_videos = [
        ("landscape_video.mp4", 1920, 1080, 60.0),
        ("portrait_video.mp4", 1080, 1920, 30.0),
        ("square_video.mp4", 1080, 1080, 45.5),
        ("ultrawide_video.mp4", 2560, 1080, 120.0),
        ("cinema_video.mp4", 1920, 817, 90.25),
    ]
    
    for filepath, width, height, duration in test_videos:
        log_video_info(logger, filepath, width, height, duration)


def test_processing_simulation(logger, video_filter):
    """Simulate a complete video processing workflow."""
    print("\n=== Testing Processing Workflow Simulation ===")
    
    logger.info("="*60)
    logger.info("Starting video processing simulation")
    
    # Simulate analyzing videos
    input_files = ["video1.mp4", "video2.mp4", "video3.mp4"]
    for i, video in enumerate(input_files):
        with LoggingContext(video_filter, video_file=video):
            logger.info(f"Analyzing video {i+1}/{len(input_files)}")
            # Simulate getting video info
            time.sleep(0.1)
            log_video_info(logger, video, 1920, 1080, 120.0)
    
    # Simulate cutting snippets
    logger.info("Starting snippet cutting phase")
    for i in range(5):
        video = input_files[i % len(input_files)]
        with LoggingContext(video_filter, 
                          video_file=video,
                          dimensions="1920x1080",
                          aspect_ratio="1.778"):
            logger.info(f"Cutting snippet {i+1}/5")
            
            # Log the FFmpeg command
            cmd = [
                "ffmpeg", "-i", video,
                "-ss", str(i * 10), "-t", "2",
                "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080",
                "-c:v", "libx264", "-preset", "fast",
                f"snippet_{i:04d}.ts"
            ]
            log_ffmpeg_command(logger, cmd)
            
            # Simulate processing time
            time.sleep(0.05)
            logger.info(f"Snippet {i+1} created successfully")
    
    # Simulate concatenation
    logger.info("Concatenating snippets")
    time.sleep(0.1)
    
    # Simulate final adjustment
    with LoggingContext(video_filter, dimensions="1920x1080", aspect_ratio="1.778"):
        logger.info("Adjusting final aspect ratio")
        logger.info("Final output: 1920x1080 (AR: 1.778)")
    
    logger.info("Processing simulation completed")
    logger.info("="*60)


def test_error_logging(logger, video_filter):
    """Test error logging with context."""
    print("\n=== Testing Error Logging ===")
    
    try:
        with LoggingContext(video_filter, video_file="problematic_video.mp4"):
            logger.info("Processing problematic video")
            # Simulate an error
            raise ValueError("Simulated video processing error")
    except ValueError:
        logger.error("Error during video processing", exc_info=True)


def main():
    """Run all logging tests."""
    print("Video Processing Logging System Test")
    print("=" * 50)
    
    # Run tests
    logger, video_filter = test_basic_logging()
    test_video_context_logging(logger, video_filter)
    test_ffmpeg_command_logging(logger)
    test_video_info_logging(logger)
    test_processing_simulation(logger, video_filter)
    test_error_logging(logger, video_filter)
    
    print("\n" + "=" * 50)
    print("Testing complete!")
    print(f"Check the log files in the 'test_logs' directory for detailed output")
    
    # List created log files
    if os.path.exists("test_logs"):
        log_files = [f for f in os.listdir("test_logs") if f.endswith(".log")]
        if log_files:
            print("\nCreated log files:")
            for log_file in sorted(log_files):
                print(f"  - {log_file}")


if __name__ == "__main__":
    main()