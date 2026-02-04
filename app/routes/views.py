"""
HTML view routes for Unitree WebRTC Connect.

This module contains routes that render HTML templates.
"""

from flask import Blueprint, render_template, Response

views_bp = Blueprint('views', __name__)


@views_bp.route('/')
def landing():
    """Render the landing page with robot management dashboard"""
    return render_template('landing.html')


@views_bp.route('/control')
def control():
    """Render the fullscreen control interface"""
    return render_template('control.html')


@views_bp.route('/test')
def test_interface():
    """Temporary route for old interface during migration (will be removed in Phase 4)"""
    return render_template('index.html')


@views_bp.route('/video_feed')
def video_feed():
    """
    Video streaming route.
    
    This route is injected with the video_service dependency when the blueprint is registered.
    """
    # video_service will be injected via current_app.config
    from flask import current_app
    video_service = current_app.config['VIDEO_SERVICE']
    
    return Response(video_service.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

