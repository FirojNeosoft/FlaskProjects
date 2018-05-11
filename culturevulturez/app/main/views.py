from alembic.autogenerate import render
from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response, jsonify
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .. import db, images
from ..models import Permission, Role, User, Post, Follow, Comment
from ..decorators import admin_required, permission_required
from .forms import EditInfoForm, AdminUserInfoEditForm, PostForm, CommentForm, SettingsForm
from datetime import datetime
import os
from werkzeug.utils import secure_filename


basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = basedir
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','webm'])

@main.route('/home', methods=["GET", "POST"])
@login_required
def home():

    user = User.query.filter_by(username=current_user.username).first()
    form = PostForm()

    # if form.validate_on_submit():
    #     post = Post(body=form.body.data, author=current_user._get_current_object())
    #     db.session.add(post)
    #     return redirect(url_for('.home'))

    show_followed = True
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        posts = current_user.followed_posts
    else:
        posts = Post.query.order_by(Post.timestamp.desc()).all()

    return render_template('index.html', user=user, form=form, posts=posts, show_followed=show_followed)

#Route to show all posts
@main.route('/explore')
@login_required
def explore():
    resp = make_response(redirect(url_for('.home')))
    resp.set_cookie('show_followed', '', max_age = 30*24*60*60)
    return resp

#Route to show followed users' posts
@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.home')))
    resp.set_cookie('show_followed', '1', max_age = 30*24*60*60)
    return resp


@main.route('/notifications/<username>')
@login_required
def notifications(username):
    user = User.query.filter_by(username=username).first()
    if current_user.username != username:
        flash('You are not authorized to access this page')
        return redirect(url_for('.profile', username=current_user.username))

    return render_template('notifications.html', user=user)

@main.route('/profile/<username>', methods=["GET", "POST"])
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)

    form = PostForm()

    if form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.profile', username=user.username))
    post = Post.query.order_by(Post.timestamp.desc()).all()

    posts = user.posts.order_by(Post.timestamp.desc()).all()

    return render_template('profile.html', user=user, posts=posts, post=post, form=form)

@main.route('/post/<int:id>', methods=["GET", "POST"])
@login_required
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, post=post, author=current_user._get_current_object())
        db.session.add(comment)
        flash('Comment added')
        return redirect(url_for('.post', id=post.id))
    comments = post.comments.order_by(Comment.timestamp.asc()).all()

    return render_template('post.html', posts=[post], form=form, comments=comments)

@main.route('/edit-post/<int:id>', methods=["GET", "POST"])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('Post Updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit-post.html', form=form)

@main.route('/post-likes/<int:id>', methods=["GET", "POST"])
@login_required
def post_likes(id):
    post = Post.query.get_or_404(id)

    return render_template('post_likes.html', post=post, id=id)

@main.route('/settings/<username>', methods=["GET", "POST"])
@login_required
def settings(username):
    user = User.query.filter_by(username=username).first()
    form = SettingsForm()

    if current_user.username != username:
        flash('You are not authorized to access this page')
        return redirect(url_for('.profile', username=current_user.username))

    if form.validate_on_submit():
            filename = images.save(request.files['profile_pic'])
            current_user.profile_pic = images.url(filename)
            current_user.nationality = form.nationality.data
            current_user.residence = form.residence.data
            current_user.postal_code = form.postal_code.data
            current_user.bio = form.bio.data
            current_user.about_me = form.about_me.data
            current_user.interests = form.interests.data

            db.session.add(current_user)
            flash('Your info has been updated')
            return redirect(url_for('.profile', username=username))

    #Display currently saved form info
    form.profile_pic.data = current_user.profile_pic
    form.nationality.data = current_user.nationality
    form.residence.data = current_user.residence
    form.postal_code.data = current_user.postal_code
    form.bio.data = current_user.bio
    form.about_me.data = current_user.about_me
    form.interests.data = current_user.interests

    return render_template('settings.html', user=user, form=form)


@main.route('/edit-info', methods=["GET", "POST"])
@login_required
def edit_info():
    #Assign form to display
    form = EditInfoForm()

    #Form fields to be edited
    if form.validate_on_submit():
            filename = images.save(request.files['profile_pic'])
            current_user.profile_pic = images.url(filename)
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.dob = form.dob.data
            current_user.gender = form.gender.data
            current_user.nationality = form.nationality.data
            current_user.residence = form.residence.data
            current_user.postal_code = form.postal_code.data
            current_user.email = form.email.data
            current_user.bio = form.bio.data
            current_user.about_me = form.about_me.data

            db.session.add(current_user)
            flash('Your info has been updated')
            return redirect(url_for('.profile', username=current_user.username))

    #Display current saved info in form fields
    form.profile_pic.data = current_user.profile_pic
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    form.dob.data = current_user.dob
    form.gender.data = current_user.gender
    form.nationality.data = current_user.nationality
    form.residence.data = current_user.residence
    form.postal_code.data = current_user.postal_code
    form.email.data = current_user.email
    form.bio.data = current_user.bio
    form.about_me.data = current_user.about_me

    return render_template('edit-info.html', form=form)

@main.route('/edit-info/<int:id>', methods=["GET", "POST"])
@login_required
@admin_required

def edit_info_admin(id):
    user = User.query.get_or_404(id)
    form = AdminUserInfoEditForm(user=user)

    if form.validate_on_submit():
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.dob = form.dob.data
        user.gender = form.gender.data
        user.nationality = form.nationality.data
        user.residence = form.residence.data
        user.postal_code = form.postal_code.data
        user.email = form.email.data
        user.about_me = form.about_me.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)

        db.session.add(user)
        flash('Profile Updated')
        return redirect(url_for('.user', username=user.username))

    #Display current saved info in form fields
    form.first_name.data = user.first_name
    form.last_name.data = user.last_name
    form.dob.data = user.dob
    form.gender.data = user.gender
    form.nationality.data = user.nationality
    form.residence.data = user.residence
    form.postal_code.data = user.postal_code
    form.email.data = user.email
    form.about_me.data = user.about_me
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id

    return render_template('edit-info-admin.html', user=user)

@main.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.home'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.profile', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % user.first_name)
    return redirect(url_for('.profile', username=username))


@main.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.home'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.Profile', username=username))
    current_user.unfollow(user)
    flash('You have unfollowed %s.' % user.first_name)
    return redirect(url_for('.profile', username=username))

@main.route('/like-post/<int:id>')
@login_required
def like_post(id):
    post = Post.query.filter_by(id=id).first()
    if post is None:
        flash('This post is invalid or has been deleted by the user')
        return redirect(url_for('.home'))
    current_user.like_post(post)
    flash("You have liked this post")
    return redirect(url_for('.post', id=id))

@main.route('/unlike-post/<int:id>')
@login_required
def unlike_post(id):
    post = Post.query.filter_by(id=id).first()
    if post is None:
        flash('This post is invalid or has been deleted by the user')
        return redirect(url_for('.home'))
    current_user.unlike_post(post)
    flash("You have unliked this post")
    return redirect(url_for('.post', id=id))

@main.route('/like-comment/<int:id>', methods=["GEt", "POST"])
@login_required
def like_comment(id):
    comment = Comment.query.filter_by(id=id).first()
    if comment is None:
        flash('This comment is invalid or has been deleted by the user')
        return redirect(url_for('.home'))
    current_user.like_comment(comment)

    return jsonify({'status': 'OK', 'like_comment': current_user.like_comment(comment)})


@main.route('/unlike-comment/<int:id>')
@login_required
def unlike_comment(id):
    comment = Comment.query.filter_by(id=id).first()
    if comment is None:
        flash('This comment is invalid or has been deleted by the user')
        return redirect(url_for('.home'))
    current_user.unlike_comment(comment)
    flash("You have unliked this comment")
    return redirect(url_for('.post', id=id))


@main.route('/followers/<username>')
@login_required
def followers(username):

    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('invalid user')
        return redirect(url_for('.home'))
    followers = user.followers
    follows = [{'user': item.follower, 'timestamp': item.timestamp} for item in followers]
    return render_template('followers.html', user=user, title='Followers of', follows=follows, endpoint='.followers')

@main.route('/following/<username>')
@login_required
def following(username):

    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('invalid user')
        return redirect(url_for('.home'))
    following = user.followed
    follows = [{'user': item.followed, 'timestamp': item.timestamp} for item in following]
    return render_template('following.html', user=user, follows=follows, endpoint='.following')

@main.route('/moderate', methods=["GET", "POST"])
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    comments = Comment.query.order_by(Comment.timestamp.desc()).all()

    return render_template('moderate.html', comments=comments)

@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate'))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate'))



@main.route('/asyncpost', methods=["GET", "POST"])
@login_required
def asyncpost():
    if request.method=='POST':
        user = User.query.filter_by(username=current_user.username).first()
        print("inside asyncpost")
        form = PostForm()
        if form.validate_on_submit():
                post = Post(body=form.body.data, author=current_user._get_current_object())
                db.session.add(post)
                print("success")
                # return "success";
        show_followed = True
        if current_user.is_authenticated:
            show_followed = bool(request.cookies.get('show_followed', ''))
        if show_followed:
            posts = current_user.followed_posts
        else:
            posts = Post.query.order_by(Post.timestamp.desc()).all()

        return render_template('_posts.html', user=user, form=form, posts=posts, show_followed=show_followed)
        # return render(render_template('_posts.html', form=form, posts=posts, show_followed=show_followed))

    else:
        return "error"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/upload_img', methods=['GET', 'POST'])
def upload_file():
    print("inside upload file")
    if request.method == 'POST':
        user = User.query.filter_by(username=current_user.username).first()
        form = PostForm()
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_url = os.path.join(basedir, filename)
            file.save(file_url)
            print(">>>file_url=", file_url)
            if form.validate_on_submit():
                post = Post(body=form.body.data,image_url = file_url,video_url = file_url, about_text=about_text, author=current_user._get_current_object())
                db.session.add(post)
                print("success")
            return redirect(url_for('.home',
                                    filename=filename))
        response = jsonify({'message': 'Error while uploading file'})
        return response
    