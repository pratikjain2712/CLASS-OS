-- Migration 002: Replace generic templates with official CBSE Maths paper patterns
-- Patterns from STANDARD BOARD PATTERN document (7 patterns: 80/50/40/30/25/20/10 marks)
-- Section E = Case-Based (SA/4M sub-questions); Assertion-Reason treated as MCQ/1M in Section A

-- Safely remove old system defaults (null out FK refs first)
UPDATE papers SET template_id = NULL
  WHERE template_id IN (SELECT id FROM paper_templates WHERE is_system_default = TRUE);

DELETE FROM paper_template_sections
  WHERE template_id IN (SELECT id FROM paper_templates WHERE is_system_default = TRUE);

DELETE FROM paper_templates WHERE is_system_default = TRUE;

-- ─────────────────────────────────────────────
-- 80 Marks  A:20×1  B:5×2  C:6×3  D:4×5  E:3×4  = 80
-- ─────────────────────────────────────────────
INSERT INTO paper_templates (name, total_marks, is_system_default) VALUES ('80 Marks', 80, TRUE);
WITH t AS (SELECT id FROM paper_templates WHERE name = '80 Marks' AND is_system_default)
INSERT INTO paper_template_sections
  (template_id, section_label, question_type, marks_per_question, question_count, sort_order)
SELECT t.id, s.lbl, s.qt, s.mpc, s.qc, s.ord FROM t,
(VALUES
  ('A','MCQ',1,20,1),
  ('B','VSA',2, 5,2),
  ('C','SA', 3, 6,3),
  ('D','LA', 5, 4,4),
  ('E','SA', 4, 3,5)
) AS s(lbl,qt,mpc,qc,ord);

-- ─────────────────────────────────────────────
-- 50 Marks  A:12×1  B:3×2  C:3×3  D:3×5  E:2×4  = 50
-- ─────────────────────────────────────────────
INSERT INTO paper_templates (name, total_marks, is_system_default) VALUES ('50 Marks', 50, TRUE);
WITH t AS (SELECT id FROM paper_templates WHERE name = '50 Marks' AND is_system_default)
INSERT INTO paper_template_sections
  (template_id, section_label, question_type, marks_per_question, question_count, sort_order)
SELECT t.id, s.lbl, s.qt, s.mpc, s.qc, s.ord FROM t,
(VALUES
  ('A','MCQ',1,12,1),
  ('B','VSA',2, 3,2),
  ('C','SA', 3, 3,3),
  ('D','LA', 5, 3,4),
  ('E','SA', 4, 2,5)
) AS s(lbl,qt,mpc,qc,ord);

-- ─────────────────────────────────────────────
-- 40 Marks  A:9×1  B:2×2  C:3×3  D:2×5  E:2×4  = 40
-- ─────────────────────────────────────────────
INSERT INTO paper_templates (name, total_marks, is_system_default) VALUES ('40 Marks', 40, TRUE);
WITH t AS (SELECT id FROM paper_templates WHERE name = '40 Marks' AND is_system_default)
INSERT INTO paper_template_sections
  (template_id, section_label, question_type, marks_per_question, question_count, sort_order)
SELECT t.id, s.lbl, s.qt, s.mpc, s.qc, s.ord FROM t,
(VALUES
  ('A','MCQ',1, 9,1),
  ('B','VSA',2, 2,2),
  ('C','SA', 3, 3,3),
  ('D','LA', 5, 2,4),
  ('E','SA', 4, 2,5)
) AS s(lbl,qt,mpc,qc,ord);

-- ─────────────────────────────────────────────
-- 30 Marks  A:7×1  B:2×2  C:3×2  D:1×5  E:2×4  = 30
-- (Section C is 2-mark for this pattern per the PDF)
-- ─────────────────────────────────────────────
INSERT INTO paper_templates (name, total_marks, is_system_default) VALUES ('30 Marks', 30, TRUE);
WITH t AS (SELECT id FROM paper_templates WHERE name = '30 Marks' AND is_system_default)
INSERT INTO paper_template_sections
  (template_id, section_label, question_type, marks_per_question, question_count, sort_order)
SELECT t.id, s.lbl, s.qt, s.mpc, s.qc, s.ord FROM t,
(VALUES
  ('A','MCQ',1, 7,1),
  ('B','VSA',2, 2,2),
  ('C','VSA',2, 3,3),
  ('D','LA', 5, 1,4),
  ('E','SA', 4, 2,5)
) AS s(lbl,qt,mpc,qc,ord);

-- ─────────────────────────────────────────────
-- 25 Marks  A:6×1  B:2×2  C:2×3  D:1×5  E:1×4  = 25
-- ─────────────────────────────────────────────
INSERT INTO paper_templates (name, total_marks, is_system_default) VALUES ('25 Marks', 25, TRUE);
WITH t AS (SELECT id FROM paper_templates WHERE name = '25 Marks' AND is_system_default)
INSERT INTO paper_template_sections
  (template_id, section_label, question_type, marks_per_question, question_count, sort_order)
SELECT t.id, s.lbl, s.qt, s.mpc, s.qc, s.ord FROM t,
(VALUES
  ('A','MCQ',1, 6,1),
  ('B','VSA',2, 2,2),
  ('C','SA', 3, 2,3),
  ('D','LA', 5, 1,4),
  ('E','SA', 4, 1,5)
) AS s(lbl,qt,mpc,qc,ord);

-- ─────────────────────────────────────────────
-- 20 Marks  A:4×1  B:2×2  C:1×3  D:1×5  E:1×4  = 20
-- ─────────────────────────────────────────────
INSERT INTO paper_templates (name, total_marks, is_system_default) VALUES ('20 Marks', 20, TRUE);
WITH t AS (SELECT id FROM paper_templates WHERE name = '20 Marks' AND is_system_default)
INSERT INTO paper_template_sections
  (template_id, section_label, question_type, marks_per_question, question_count, sort_order)
SELECT t.id, s.lbl, s.qt, s.mpc, s.qc, s.ord FROM t,
(VALUES
  ('A','MCQ',1, 4,1),
  ('B','VSA',2, 2,2),
  ('C','SA', 3, 1,3),
  ('D','LA', 5, 1,4),
  ('E','SA', 4, 1,5)
) AS s(lbl,qt,mpc,qc,ord);

-- ─────────────────────────────────────────────
-- 10 Marks  A:1×1  B:1×2  C:1×3  E:1×4  (no Section D)  = 10
-- ─────────────────────────────────────────────
INSERT INTO paper_templates (name, total_marks, is_system_default) VALUES ('10 Marks', 10, TRUE);
WITH t AS (SELECT id FROM paper_templates WHERE name = '10 Marks' AND is_system_default)
INSERT INTO paper_template_sections
  (template_id, section_label, question_type, marks_per_question, question_count, sort_order)
SELECT t.id, s.lbl, s.qt, s.mpc, s.qc, s.ord FROM t,
(VALUES
  ('A','MCQ',1, 1,1),
  ('B','VSA',2, 1,2),
  ('C','SA', 3, 1,3),
  ('E','SA', 4, 1,4)
) AS s(lbl,qt,mpc,qc,ord);
