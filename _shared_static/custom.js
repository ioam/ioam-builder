function expand(e) {
	if (e.target.parentNode.tagName.toLowerCase() != "dl") {
		var p = e.target.parentNode.parentNode;
	} else {
		var p = e.target.parentNode;
	}

	//if (p.className.indexOf

	if (p.className == "class rm_collapsed")
		p.className = "class rm_expanded";
	else if (p.className == "class rm_expanded")
		p.className = "class rm_collapsed";
}

function hook_classes() {
	$("dl.class dt").click(expand);
	$("dl.class").addClass("rm_collapsed");
	$.each($('code'), function(index, code) {
		code.textContent = code.textContent.trim()
	});
	$.each($('.output_subarea').find('pre'), function(index, pre) {
		pre.textContent = pre.textContent.split('&apos;').join("'");
	});
}

$(document).ready(hook_classes);

// Patch doctools.js alias, restoring underscore.js
_ = $u;
