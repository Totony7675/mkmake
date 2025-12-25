---
layout: page
title: "Product Categories"
permalink: /tags/
---

{% assign rawtags = "" %}
{% for post in site.posts %}
  {% assign tsize = post.tags | size %}
  {% if tsize > 0 %}
    {% for tag in post.tags %}
      {% assign rawtags = rawtags | append: "," | append: tag %}
    {% endfor %}
  {% endif %}
{% endfor %}

{% assign tags = rawtags | split: "," | uniq | sort %}

<div class="tag-cloud">
  {% for tag in tags %}
    <a href="#{{ tag | slugify }}" class="btn btn-outline-primary m-1">{{ tag | capitalize }}</a>
  {% endfor %}
</div>

<hr>

{% for tag in tags %}
  <h2 id="{{ tag | slugify }}">{{ tag | capitalize }}</h2>
  <div class="row">
    {% for post in site.posts %}
      {% if post.tags contains tag %}
        <div class="col-md-4 mb-4">
          <div class="card">
            <img src="{{ post.thumbnail-img }}" class="card-img-top" alt="{{ post.title }}">
            <div class="card-body">
              <h5 class="card-title">{{ post.title }}</h5>
              <a href="{{ post.url | relative_url }}" class="btn btn-sm btn-primary">View Details</a>
            </div>
          </div>
        </div>
      {% endif %}
    {% endfor %}
  </div>
{% endfor %}