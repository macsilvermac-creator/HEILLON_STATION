"""Tier & quota domain — freemium infrastructure for Heillon substrate.

A organization has a tier (free/pro/team/enterprise) that controls quota
(monthly HDR limit) and retention (auto-purge of old HDRs for free tier).

Quota is enforced at HDR creation; webhooks from the external billing site
update tier in real time.
"""
