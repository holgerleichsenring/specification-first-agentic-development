export default function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy({ "src/static": "." });

  // vercel.json sets trailingSlash false, so a page answers without its trailing slash.
  eleventyConfig.addFilter("canonicalPath", (url) => (url === "/" ? "/" : String(url).replace(/\/$/, "")));

  return {
    dir: {
      input: "src",
      includes: "_includes",
      data: "_data",
      output: "_site"
    },
    templateFormats: ["njk"],
    htmlTemplateEngine: "njk"
  };
}
