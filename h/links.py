"""Provides links to different representations of annotations."""

from urllib.parse import unquote, urldefrag, urljoin, urlparse


def pretty_link(url):
    """
    Return a nicely formatted version of a URL.

    This strips off 'visual noise' from the URL including common schemes
    (HTTP, HTTPS), domain prefixes ('www.') and query strings.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        return url
    netloc = parsed.netloc
    netloc = netloc.removeprefix("www.")
    return unquote(netloc + parsed.path)


def html_link(request, annotation):
    """Return a link to an HTML representation of the given annotation, or None."""
    is_third_party_annotation = annotation.authority != request.default_authority
    if is_third_party_annotation:
        # We don't currently support HTML representations of third party
        # annotations.
        return None
    return request.route_url("annotation", id=annotation.id)


def incontext_link(request, annotation):
    """
    Generate a link to an annotation on the page where it was made.

    If a bouncer (`h.bouncer_url`) is configured, this is a link to the bouncer.

    Otherwise it links straight to the page with an `#annotations:<id>`
    fragment, which the client reads on load to select the annotation. This
    works for pages that embed the client. Returns None if the annotation
    wasn't made on a web (http or https) page.
    """
    bouncer_url = request.registry.settings.get("h.bouncer_url")
    web_uri = _web_uri(annotation)

    if not bouncer_url:
        if web_uri is None:
            return None
        # The client only recognizes the fragment at the end of the URL, so
        # replace any fragment the page URL already has.
        return f"{urldefrag(web_uri).url}#annotations:{annotation.thread_root_id}"

    link = urljoin(bouncer_url, annotation.thread_root_id)
    if web_uri is not None:
        # We can't use urljoin here, because if it detects the second argument
        # is a URL it will discard the base URL, breaking the link entirely.
        link += "/" + web_uri[web_uri.index("://") + 3 :]

    return link


def _web_uri(annotation):
    """Return the web (http or https) URL of the annotated page, or None."""
    uri = annotation.target_uri
    if uri.startswith(("http://", "https://")):
        return uri

    if uri.startswith("urn:x-pdf:") and annotation.document:
        for docuri in annotation.document.document_uris:
            if docuri.uri.startswith(("http://", "https://")):
                return docuri.uri

    return None


def json_link(request, annotation):
    return request.route_url("api.annotation", id=annotation.id)


def jsonld_id_link(request, annotation):
    return request.route_url("annotation", id=annotation.id)


def includeme(config):  # pragma: no cover
    # Add an annotation link generator for the `annotation` view -- this adds a
    # named link called "html" to API rendered views of annotations. See
    # :py:mod:`h.presenters` for details.
    config.add_annotation_link_generator("html", html_link)

    # Add an annotation link generator for viewing annotations in context on
    # the page on which they were made.
    config.add_annotation_link_generator("incontext", incontext_link)

    # Add a default 'json' link type
    config.add_annotation_link_generator("json", json_link)

    # Add a 'jsonld_id' link type for generating the "id" field for JSON-LD
    # annotations. This is hidden, and so not rendered in the annotation's
    # "links" field.
    config.add_annotation_link_generator("jsonld_id", jsonld_id_link, hidden=True)
