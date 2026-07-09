$(document).ready(function() {
    function a(a) {
        return a.children(".drawer").children("h2").addClass("expand"), a.children(".drawer").children("div").show(), a.children(".drawer").children("article").show(), !1
    }

    function b(a) {
        return a.children(".drawer").children("h2").removeClass("expand"), a.children(".drawer").children("div").hide(), a.children(".drawer").children("article").hide(), !1
    }

    function c(a) {
        a.find(".drawer-toggle a").each(function() {
            element = $(this), element.hasClass("expand") ? element.html("Collapse All") : element.html("Expand All"), element.toggleClass("expand")
        })
    }
    $(".drawer").each(function() {
        var d = $(this);
        d.wrap('<div class="drawer-wrapper main-section-content"/>');
        var e = d.parent(),
            f = '<div class="drawer-toggle"><a href="#" class="expand">Expand All</a></div>';
        e.prepend(f), e.append(f), d.children("div").toggle(), d.children("article").toggle(), d.children("h2").click(function() {
            return $(this).toggleClass("expand"), $(this).next().toggle(), $(this).hasClass("expand") && (window.location.hash = $(this).find("a").text().replace(/\s/g, "-").substring(0, 31)), !1
        }), e.find(".drawer-toggle a").click(function() {
            return $(this).hasClass("expand") ? a(e) : b(e), c(e), window.history && window.history.pushState ? window.history.pushState("", "", window.location.pathname) : window.location.href = window.location.href.replace(/#.*$/, "#"), !1
        }), $(window).on("load", function() {
            d.children("h2").each(function() {
                if (window.location.hash == "#" + $(this).find("a").text().replace(/\s/g, "-").substring(0, 31)) {
                    var a = $(this).offset();
                    $(this).toggleClass("expand").next().toggle(), setTimeout(function() {
                        window.scrollTo(0, a.top)
                    }, 50)
                }
            })
        })
    })
})