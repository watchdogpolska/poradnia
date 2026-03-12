"use strict";

const fs = require("fs");
const gulp = require("gulp");
const concat = require("gulp-concat");
const livereload = require("gulp-livereload");
const cleanCSS = require("gulp-clean-css");
const rename = require("gulp-rename");
const sass = require("gulp-sass")(require("sass"));
const uglify = require("gulp-uglify");
const postcss = require("gulp-postcss");
const autoprefixer = require("autoprefixer");
const json = JSON.parse(fs.readFileSync("./package.json"));

// ----------------------------------
// Configuration
// ----------------------------------
const appName = json.name;

const path = {
  npm: "./node_modules/",
  app: `./${appName}`,
  assets: `./${appName}/assets`,
  static: `./${appName}/static`,
  staticfiles: "./staticfiles",
};

const config = {
  path,
  scss: {
    input: [
      path.npm + "/@fortawesome/fontawesome-free/css/fontawesome.css",
      path.npm + "/@fortawesome/fontawesome-free/css/solid.css",
      path.npm + "/@fortawesome/fontawesome-free/css/regular.css",
      path.npm + "/@fortawesome/fontawesome-free/css/brands.css",
      path.assets + "/scss/style.scss",
      path.npm + "/datatables.net-buttons-dt/css/buttons.dataTables.css",
      path.npm + "/datatables.net-dt/css/jquery.dataTables.css",
    ],
    include: [
      path.npm,
      path.npm + "/pikaday-time/scss/",
      path.staticfiles,
      path.assets + "/scss/",
    ],
    output: {
      dir: path.static + "/css",
      filename: "style.css",
    },
    watch: [path.assets + "/scss/**/*.scss"],
  },
  images: {
    input: [path.npm + "/datatables.net-dt/images/sort*.*"],
    output: path.static + "/images",
  },
  icons: {
    input: [path.npm + "/@fortawesome/fontawesome-free/webfonts/**/*.*"],
    output: path.static + "/webfonts",
  },
  script: {
    input: [
      path.npm + "/jquery/dist/jquery.js",
      path.npm + "/bootstrap-sass/assets/javascripts/bootstrap/tab.js",
      path.npm + "/bootstrap-sass/assets/javascripts/bootstrap/tooltip.js",
      path.npm + "/bootstrap-sass/assets/javascripts/bootstrap/modal.js",
      path.staticfiles + "/tasty_feedback/style.js",
      path.npm + "/moment/moment.js",
      path.npm + "/moment/locale/pl.js",
      path.npm + "/pikaday-time/pikaday.js",
      path.npm + "/patternomaly/dist/patternomaly.js",
      path.assets + "/js/*.js",
      path.app + "/navsearch/static/navsearch/*.js",
      path.npm + "/datatables.net/js/jquery.dataTables.js",
      path.npm + "/datatables.net-dt/js/dataTables.dataTables.js",
      path.npm + "/datatables.net-buttons/js/dataTables.buttons.js",
      path.staticfiles + "/ajax_datatable/js/utils.js",
      path.app + "/cases/static/cases/case_datatbles.js",
      path.app + "/advicer/static/advicer/advice_datatbles.js",
      path.app + "/letters/static/letters/letters_datatbles.js",
      path.app + "/events/static/events/events_datatbles.js",
    ],
    output: {
      dir: path.static + "/js",
      filename: "script.js",
    },
    watch: [path.assets + "/js/*.js"],
  },
};

// ----------------------------------
// Tasks
// ----------------------------------

function icons() {
  return gulp.src(config.icons.input, { encoding: false })
    .pipe(gulp.dest(config.icons.output));
}

function images() {
  return gulp.src(config.images.input, { encoding: false })
    .pipe(gulp.dest(config.images.output));
}

function js() {
  return gulp.src(config.script.input, { allowEmpty: true })
    .pipe(concat(config.script.output.filename))
    .pipe(gulp.dest(config.script.output.dir))
    .pipe(livereload())
    .pipe(uglify())
    .pipe(rename({ extname: ".min.js" }))
    .pipe(gulp.dest(config.script.output.dir))
    .pipe(livereload());
}

function scss() {
  return gulp.src(config.scss.input, { allowEmpty: true })
    .pipe(
      sass({
        style: "expanded",
        includePaths: config.scss.include,
      }).on("error", sass.logError)
    )
    .pipe(postcss([autoprefixer()]))
    .pipe(concat(config.scss.output.filename))
    .pipe(gulp.dest(config.scss.output.dir))
    .pipe(livereload())
    .pipe(cleanCSS({ compatibility: "ie8" }))
    .pipe(rename({ extname: ".min.css" }))
    .pipe(gulp.dest(config.scss.output.dir))
    .pipe(livereload());
}

function watchFiles() {
  livereload.listen();
  gulp.watch(config.scss.watch, scss);
  gulp.watch(config.script.watch, js);
}

// ----------------------------------
// Build & default
// ----------------------------------
const build = gulp.series(images, icons, js, scss);
const dev = gulp.series(build, watchFiles);

exports.icons = icons;
exports.images = images;
exports.js = js;
exports.scss = scss;
exports.build = build;
exports.watch = watchFiles;
exports.default = build;
