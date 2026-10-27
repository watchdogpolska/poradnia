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
      path.npm + "/datatables.net-dt/css/dataTables.dataTables.css",
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
  wcagScss: {
    input: [path.assets + "/scss/wcag.scss"],
    include: [path.npm, path.staticfiles, path.assets + "/scss/"],
    output: {
      dir: path.static + "/css",
      filename: "wcag.css",
    },
    watch: [path.assets + "/scss/wcag.scss"],
  },
  icons: {
    input: [path.npm + "/@fortawesome/fontawesome-free/webfonts/**/*.*"],
    output: path.static + "/webfonts",
  },
  script: {
    input: [
      path.npm + "/bootstrap/dist/js/bootstrap.bundle.js",
      path.npm + "/htmx.org/dist/htmx.js",
      path.staticfiles + "/tasty_feedback/style.js",
      path.npm + "/moment/moment.js",
      path.npm + "/moment/locale/pl.js",
      path.npm + "/pikaday-time/pikaday.js",
      path.npm + "/patternomaly/dist/patternomaly.js",
      path.assets + "/js/*.js",
      // wcag.js is bundled separately (see wcagScript below) so that
      // style.css/.min.css + script.js/.min.js stay byte-identical whether
      // or not WCAG mode exists - that's what keeps baseline/assets.sha256
      // stable for logs/wcag's baseline-diff gate.
      "!" + path.assets + "/js/wcag.js",
      path.npm + "/datatables.net/js/dataTables.js",
      path.npm + "/datatables.net-dt/js/dataTables.dataTables.js",
      path.staticfiles + "/ajax_datatable/js/utils.js",
      path.app + "/cases/static/cases/case_datatables.js",
      path.app + "/advicer/static/advicer/advice_datatables.js",
      path.app + "/letters/static/letters/letters_datatables.js",
      path.app + "/letters/static/letters/attachment_dropzone.js",
      path.app + "/letters/static/letters/attachment_formset.js",
      path.app + "/events/static/events/events_datatables.js",
      path.app + "/users/static/users/users_datatables.js",
      path.app + "/dashboard/static/dashboard/dashboard.js",
      ],

    output: {
      dir: path.static + "/js",
      filename: "script.js",
    },
    watch: [path.assets + "/js/*.js"],
  },
  wcagScript: {
    input: [path.assets + "/js/wcag.js"],
    output: {
      dir: path.static + "/js",
      filename: "wcag.js",
    },
    watch: [path.assets + "/js/wcag.js"],
  },
};

// ----------------------------------
// Tasks
// ----------------------------------

function icons() {
  return gulp.src(config.icons.input, { encoding: false })
    .pipe(gulp.dest(config.icons.output));
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
        loadPaths: config.scss.include,
        quietDeps: true,
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

function wcagScss() {
  return gulp.src(config.wcagScss.input, { allowEmpty: true })
    .pipe(
      sass({
        style: "expanded",
        loadPaths: config.wcagScss.include,
        quietDeps: true,
      }).on("error", sass.logError)
    )
    .pipe(postcss([autoprefixer()]))
    .pipe(concat(config.wcagScss.output.filename))
    .pipe(gulp.dest(config.wcagScss.output.dir))
    .pipe(livereload())
    .pipe(cleanCSS({ compatibility: "ie8" }))
    .pipe(rename({ extname: ".min.css" }))
    .pipe(gulp.dest(config.wcagScss.output.dir))
    .pipe(livereload());
}

function wcagJs() {
  return gulp.src(config.wcagScript.input, { allowEmpty: true })
    .pipe(concat(config.wcagScript.output.filename))
    .pipe(gulp.dest(config.wcagScript.output.dir))
    .pipe(livereload())
    .pipe(uglify())
    .pipe(rename({ extname: ".min.js" }))
    .pipe(gulp.dest(config.wcagScript.output.dir))
    .pipe(livereload());
}

function watchFiles() {
  livereload.listen();
  gulp.watch(config.scss.watch, scss);
  gulp.watch(config.script.watch, js);
  gulp.watch(config.wcagScss.watch, wcagScss);
  gulp.watch(config.wcagScript.watch, wcagJs);
}

// ----------------------------------
// Build & default
// ----------------------------------
const build = gulp.series(icons, js, scss, wcagJs, wcagScss);
const dev = gulp.series(build, watchFiles);

exports.icons = icons;
exports.js = js;
exports.scss = scss;
exports.wcagJs = wcagJs;
exports.wcagScss = wcagScss;
exports.build = build;
exports.watch = watchFiles;
exports.default = build;
