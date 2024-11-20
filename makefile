.PHONY: clean tiles

clean:
	rm -rf out/tiles

tiles: clean
	vips dzsave ./all-map-mini-test.png out/tiles --layout google --background 0
# --suffix .png[compression=9]