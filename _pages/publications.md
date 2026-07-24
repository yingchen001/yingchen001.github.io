---
layout: page
permalink: /publications/
title: publications
description: >
  <sup>†</sup> corresponding author &nbsp;·&nbsp; <sup>*</sup> equal contribution &nbsp;·&nbsp; <a href="https://scholar.google.com/citations?user=0cet0X8AAAAJ" target="_blank" rel="noopener noreferrer">Full list on Google Scholar</a>
years: [2026, 2025, 2024, 2023, 2022, 2021]
nav: true
nav_order: 1
---
<!-- _pages/publications.md -->
<div class="publications">

{%- for y in page.years %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f {{ site.scholar.bibliography }} -q @*[year={{y}}]* %}
{% endfor %}

</div>
