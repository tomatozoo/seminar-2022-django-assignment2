from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from .serializers import PostListSerializer, PostDetailSerializer, ClapseSerializer, TagCommentSerializer, TagPostSerializer, CommentDetailSerializer, CommentListSerializer
from .models import Post, Clapse, Comment, Tag
from .pagination import PostPagination, CommentPagination, TagPagination
from user.models import User as user_models
from user import serializers as user_serializers
from user.permissions import IsAuthorOrReadOnly
from notification import views as notification_views
import re

# Create your views here.


class PostList(APIView):

    permission_class = IsAuthorOrReadOnly
    pagination_class = PostPagination

    def get(self, request, format=None):
        post = Post.objects.all()

        serializer = PostListSerializer(
            post, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = PostDetailSerializer(data=request.data)
        if serializer.is_valid():
            created_by = request.user
            summary_for_listing = request.data["description"][:300]
            n_min_read = 1 + len(request.data["description"]) / 200
            post = serializer.save(
                created_by=created_by,
                summary_for_listing=summary_for_listing,
                n_min_read=n_min_read
            )
            create_tag = request.data.get("create_tag")
            tag_regex = re.findall(r'#([0-9a-zA-Z가-힣]*)', create_tag)
            tags_list = [Tag.objects.get_or_create(
                name=t) for t in tag_regex]
            for tag, bool in tags_list:
                post.tags.add(tag.pk)
            post.save()
            serializer = PostDetailSerializer(
                post,
                context={"request": request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )


class PostDetail(APIView):

    permission_class = (IsAuthorOrReadOnly, )

    def get(self, request, pk, format=None):
        post = Post.objects.get(pk=pk)
        serializer = PostDetailSerializer(
            post, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, format=None):

        created_by = request.user
        post = Post.objects.get(pk=pk)
        if post is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = PostDetailSerializer(
            post, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save(created_by=created_by)
            return Response(data=serializer.data, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):

        created_by = request.user
        post = Post.objects.get(pk=pk)
        if post is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentList(APIView):

    permission_class = (IsAuthorOrReadOnly, )
    pagination_class = CommentPagination

    def post(self, request, pk, format=None):
        post = Post.objects.get(pk=pk)

        if post is None:
            print("no post exist")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        parent_comment = request.data.get("parent_comment")
        if parent_comment is not None:
            try:
                parent_comment = Comment.objects.get(pk=parent_comment)
            except:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = CommentDetailSerializer(data=request.data)
        if serializer.is_valid():
            created_by = request.user
            parent_comment = request.data.get("parent_comment", None)

            comment = serializer.save(
                created_by=created_by,
                post=post,
                parent_comment=parent_comment
            )

            create_tag = request.data.get("create_tag")
            tag_regex = re.findall(r'#([0-9a-zA-Z가-힣]*)', create_tag)
            tags_list = [Tag.objects.get_or_create(name=t) for t in tag_regex]
            for tag, bool in tags_list:
                comment.tags.add(tag.pk)
            comment.save()

            notification_views.create_notification(
                created_by, post.created_by, 'comment', post, serializer.data.get(
                    'content')
            )

            serializer = CommentDetailSerializer(
                comment,
                context={"request": request},
            )
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk, format=None):
        comment = Comment.objects.filter(post=pk)

        if comment is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = CommentListSerializer(
            comment, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentDetail(APIView):

    permission_class = (IsAuthorOrReadOnly, )

    def put(self, request, pk, pk2, format=None):
        comment = Comment.objects.get(post=pk, pk=pk2)
        is_updated = True

        if comment is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = CommentDetailSerializer(
            comment, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save(is_updated=is_updated)
            return Response(data=serializer.data, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, pk2, format=None):
        comment = Comment.objects.get(post=pk, pk=pk2)

        if comment is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClapseList(APIView):

    permission_class = (IsAuthorOrReadOnly, )

    def get(self, request, pk, format=None):
        clapse = Clapse.objects.filter(post__pk=pk)
        clapse_created_by_ids = clapse.values('created_by')
        print(clapse_created_by_ids)
        created_by = user_models.objects.filter(
            pk__in=clapse_created_by_ids)
        serializer = user_serializers.UserSerializer(
            created_by, many=True, context={'request': request}
        )
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk, format=None):
        created_by = request.user

        try:
            find_post = Post.objects.get(pk=pk)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            preexisting_clapse = Clapse.objects.get(
                post=find_post,
                created_by=created_by
            )
            return Response(status=status.HTTP_304_NOT_MODIFIED)
        except:
            clapse = Clapse.objects.create(
                post=find_post,
                created_by=created_by
            )
            clapse.save()
            notification_views.create_notification(
                created_by, find_post.created_by, 'like', find_post
            )
            return Response(status=status.HTTP_201_CREATED)


class UnClapseList(APIView):

    permission_class = (IsAuthorOrReadOnly, )

    def delete(self, request, pk, format=None):
        created_by = request.user

        try:
            find_post = Post.objects.get(pk=pk)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            preexisting_clapse = Clapse.objects.get(
                created_by=created_by,
                post=find_post
            )
            preexisting_clapse.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except:
            return Response(status=status.HTTP_304_NOT_MODIFIED)


class TagPostList(APIView):

    permission_class = (IsAuthorOrReadOnly, )
    pagination_class = TagPagination

    def get(self, request, tagname, format=None):

        try:
            tag = Tag.objects.get(name=tagname)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            post = Post.objects.filter(tags=tag)
            serializer = PostListSerializer(
                post, many=True, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response(status=status.HTTP_404_NOT_FOUND)


class TagCommentList(APIView):

    permission_class = (IsAuthorOrReadOnly, )
    pagination_class = TagPagination

    def get(self, request, tagname, format=None):

        try:
            tag = Tag.objects.get(name=tagname)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            comment = Comment.objects.filter(tags=tag)
            serializer = CommentListSerializer(
                comment, many=True, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        except:
            return Response(status=status.HTTP_404_NOT_FOUND)
